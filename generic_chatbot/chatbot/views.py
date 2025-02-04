from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async
from rest_framework.response import Response
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from kani import Kani
from server.engine import initialize_engine
from .models import Conversation, Bot, Utterance
import json
from datetime import datetime

def health_check(request):
    return JsonResponse({"status": "ok"})


# Load config.json
def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise RuntimeError("Configuration file 'config.json' not found.")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding 'config.json': {e}")


# Initialize engine and bots dynamically
config = load_config()
engine = initialize_engine(config)

@method_decorator(csrf_exempt, name='dispatch')
class InitializeConversationAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Parse JSON from the request body
            data = json.loads(request.body)
            bot_name = data.get("bot_name")
            participant_id = data.get("participant_id")
            prompt = data.get("prompt","n/a")
            study_name = data.get("study_name","n/a")
            user_group = data.get("user_group","n/a")

            # Validate required fields
            if not bot_name or not participant_id:
                return JsonResponse(
                    {"error": "Both 'bot_name' and 'participant_id' are required."}, status=400
                )

            # Fetch the bot
            try:
                bot = Bot.objects.get(name=bot_name)
            except Bot.DoesNotExist:
                return JsonResponse(
                    {"error": f"No bot found with the name '{bot_name}'."}, status=404
                )

            # Check for an existing conversation
            existing_conversation = Conversation.objects.filter(
                participant_id=participant_id, bot_name=bot.name
            ).order_by("-started_time").first()

            if existing_conversation:
                return JsonResponse(
                    {
                        "conversation_id": existing_conversation.conversation_id,
                        "message": "Existing conversation found."
                    },
                    status=200,
                )

            # Generate a new conversation ID
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            conversation_id = f"{participant_id}_{current_time}"

            # Create a new conversation
            Conversation.objects.create(
                conversation_id=conversation_id,
                bot_name=bot.name,
                prompt = prompt, 
                participant_id=participant_id,
                study_name = study_name,
                user_group = user_group,
                started_time=datetime.now(),
            )

            return JsonResponse(
                {
                    "conversation_id": conversation_id,
                    "message": "Conversation initialized successfully."
                },
                status=200,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
        except Exception as e:
            print(f"Unhandled exception: {e}")
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)

#save chat
async def save_chat_to_db(conversation_id, speaker_id, text, bot_name=None, participant_id=None):
    try:
        # Wrap the ORM call to get the conversation using sync_to_async
        conversation = await sync_to_async(Conversation.objects.get)(conversation_id=conversation_id)
        print(f"Found conversation {conversation.conversation_id}, inserting message...")

        # Wrap the ORM call to create the Utterance
        await sync_to_async(Utterance.objects.create)(
            conversation=conversation,  # This links to your saved conversation object
            speaker_id=speaker_id,
            bot_name=bot_name,
            participant_id=participant_id,  # If your model supports participant_id (or remove if not)
            text=text
        )
        print("✅ Successfully saved message to Utterance table.")

    except Conversation.DoesNotExist:
        print(f"❌ Conversation with ID {conversation_id} not found.")
    except Exception as e:
        print(f"❌ Failed to save message to Utterance table: {e}")

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(View):
    async def post(self, request, *args, **kwargs):
        try:
            # Parse JSON payload
            data = json.loads(request.body)
            message = data.get('message', '')
            bot_name = data.get('bot_name', '')
            conversation_id = data.get('conversation_id', None)
            participant_id = data.get('participant_id', None)  # Qualtrics participant user_id

            if not message or not bot_name or not conversation_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch bot using sync_to_async
            bot = await sync_to_async(Bot.objects.get)(name=bot_name)

            kani = Kani(engine, system_prompt=bot.prompt)
            # Process bot response asynchronously
            response = await kani.chat_round(message)
            response_text = response.text

            # Save user message to the Utterance table
            await save_chat_to_db(
                conversation_id=conversation_id,
                speaker_id="user",
                text=message,
                bot_name=None,  # User message, no bot name
                participant_id=participant_id
            )

            # Save bot response to the Utterance table
            await save_chat_to_db(
                conversation_id=conversation_id,
                speaker_id="assistant",
                text=response_text,
                bot_name=bot.name,  # Bot's name
                participant_id=None
            )

            # Return the bot's response
            return JsonResponse({'message': message, 'response': response_text, 'bot_name': bot_name}, status=200)
        except Exception as e:
            print(f"Error in ChatbotAPIView: {e}")
            return JsonResponse({'error': str(e)}, status=500)

class ListBotsAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            # Fetch bot names from the database
            bots = Bot.objects.values_list("name", flat=True)
            return JsonResponse({"bot_names": list(bots)}, status=200)
        except Exception as e:
            print(f"Error in ListBotsAPIView: {e}")
            return JsonResponse({"error": str(e)}, status=500)
