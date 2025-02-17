import json
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
from server.engine import initialize_engine, get_or_create_engine
from .models import Conversation, Bot, Utterance
from datetime import datetime
from kani import Kani

# Dictionary to store per-engine configurations
engine_instances = {}

def health_check(request):
    return JsonResponse({"status": "ok"})

@method_decorator(csrf_exempt, name='dispatch')
class InitializeConversationAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            print("[DEBUG] Entering InitializeConversationAPIView.post()...")

            # Attempt to parse JSON
            try:
                data = json.loads(request.body)
            except Exception as parse_error:
                print(f"[DEBUG] JSON parse error: {parse_error}")
                return JsonResponse({"error": "Invalid JSON in request body."}, status=400)

            print(f"[DEBUG] Received JSON data: {data}")

            bot_name = data.get("bot_name")
            participant_id = data.get("participant_id")
            initial_utterance = data.get("initial_utterance", "n/a")
            study_name = data.get("study_name", "n/a")
            user_group = data.get("user_group", "n/a")
            survey_id = data.get("survey_id", "n/a")
            survey_meta_data = data.get("survey_meta_data", "n/a")

            print(f"[DEBUG] bot_name={bot_name}, participant_id={participant_id}")
            print(f"[DEBUG] initial_utterance={initial_utterance}, study_name={study_name}, user_group={user_group}")
            print(f"[DEBUG] survey_id={survey_id}, survey_meta_data={survey_meta_data}")

            if not bot_name or not participant_id:
                print("[DEBUG] Missing 'bot_name' or 'participant_id'. Returning error.")
                return JsonResponse(
                    {"error": "Both 'bot_name' and 'participant_id' are required."}, 
                    status=400
                )

            # Fetch the bot
            try:
                bot = Bot.objects.get(name=bot_name)
                print(f"[DEBUG] Found bot with name '{bot_name}'")
            except Bot.DoesNotExist:
                print(f"[DEBUG] Bot.DoesNotExist: '{bot_name}' not found in DB.")
                return JsonResponse({"error": f"No bot found with the name '{bot_name}'."}, status=404)
            except Exception as bot_fetch_error:
                print(f"[DEBUG] Unexpected error fetching bot: {bot_fetch_error}")
                return JsonResponse({"error": "Error fetching the bot from the database."}, status=500)

            # Ensure the engine is initialized
            try:
                print(f"[DEBUG] Initializing engine for bot model_type={bot.model_type}, model_id={bot.model_id}")
                get_or_create_engine(bot.model_type, bot.model_id, engine_instances)
            except Exception as engine_error:
                print(f"[DEBUG] Engine initialization error: {engine_error}")
                return JsonResponse({"error": "Failed to initialize the engine."}, status=500)

            # Generate a conversation ID
            conversation_id = f"{participant_id}__{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"[DEBUG] Generated conversation ID: {conversation_id}")

            # Create a conversation entry
            try:
                Conversation.objects.create(
                    conversation_id=conversation_id,
                    bot_name=bot.name,
                    participant_id=participant_id,
                    initial_utterance=initial_utterance,
                    study_name=study_name,
                    user_group=user_group,
                    survey_id=survey_id,
                    survey_meta_data=survey_meta_data,
                    started_time=datetime.now(),
                )
                print("[DEBUG] Conversation object created successfully.")
            except Exception as create_conv_error:
                print(f"[DEBUG] Error creating Conversation object: {create_conv_error}")
                return JsonResponse({"error": "Failed to create Conversation."}, status=500)

            return JsonResponse(
                {"conversation_id": conversation_id, "message": "Conversation initialized successfully."}, 
                status=200
            )

        except Exception as e:
            print(f"[DEBUG] Unhandled exception in InitializeConversationAPIView: {e}")
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
            participant_id = data.get('participant_id', None)

            if not message or not bot_name or not conversation_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch bot using sync_to_async
            bot = await sync_to_async(Bot.objects.get)(name=bot_name)

            # 2) Retrieve or create engine, passing the global dictionary 
            engine = get_or_create_engine(bot.model_type, bot.model_id, engine_instances)

            kani = Kani(engine, system_prompt=bot.prompt)
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


            return JsonResponse({'message': message, 'response': response_text, 'bot_name': bot_name}, status=200)

        except Exception as e:
            print(f"Error in ChatbotAPIView: {e}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ListBotsAPIView(View):
    """
    GET  -> List all bots
    POST -> Create a new bot
    """

    def get(self, request, *args, **kwargs):
        try:
            # Return all bots as a list of dicts
            bots = Bot.objects.values("id", "name", "model_type", "model_id", "prompt")
            return JsonResponse({"bots": list(bots)}, status=200)
        except Exception as e:
            print(f"Error in ListCreateBotsAPIView GET: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def post(self, request, *args, **kwargs):
        """
        Create a new Bot in the database.
        Expects JSON body like:
        {
          "name": "MyBot",
          "model_type": "OpenAI",
          "model_id": "gpt-4",
          "prompt": "..."
        }
        """
        try:
            data = json.loads(request.body)
            name = data.get("name")
            model_type = data.get("model_type")
            model_id = data.get("model_id")
            prompt = data.get("prompt", "")

            # Minimal validation
            if not name or not model_type or not model_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Create and save a new Bot
            bot = Bot.objects.create(
                name=name,
                model_type=model_type,
                model_id=model_id,
                prompt=prompt
            )

            return JsonResponse(
                {
                    "id": bot.id,
                    "name": bot.name,
                    "model_type": bot.model_type,
                    "model_id": bot.model_id,
                    "prompt": bot.prompt,
                },
                status=201
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except Exception as e:
            print(f"Error in ListCreateBotsAPIView POST: {e}")
            return JsonResponse({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class BotDetailAPIView(View):
    """
    GET    -> Retrieve single bot by ID (optional, if your front-end ever needs it)
    PUT    -> Update an existing bot by ID
    DELETE -> Delete a bot by ID
    """

    def get(self, request, pk, *args, **kwargs):
        """Optional: get a single bot's details by ID."""
        try:
            bot = Bot.objects.get(pk=pk)
            data = {
                "id": bot.id,
                "name": bot.name,
                "model_type": bot.model_type,
                "model_id": bot.model_id,
                "prompt": bot.prompt,
            }
            return JsonResponse(data, status=200)
        except Bot.DoesNotExist:
            return JsonResponse({"error": "Bot not found"}, status=404)
        except Exception as e:
            print(f"Error in BotDetailAPIView GET: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def put(self, request, pk, *args, **kwargs):
        """Update an existing bot by ID."""
        try:
            bot = Bot.objects.get(pk=pk)
        except Bot.DoesNotExist:
            return JsonResponse({"error": "Bot not found"}, status=404)

        try:
            data = json.loads(request.body)
            bot.name = data.get("name", bot.name)
            bot.model_type = data.get("model_type", bot.model_type)
            bot.model_id = data.get("model_id", bot.model_id)
            bot.prompt = data.get("prompt", bot.prompt)
            bot.save()

            return JsonResponse({"message": "Bot updated successfully."}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except Exception as e:
            print(f"Error in BotDetailAPIView PUT: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def delete(self, request, pk, *args, **kwargs):
        """Delete an existing bot by ID."""
        try:
            bot = Bot.objects.get(pk=pk)
            bot.delete()
            # 204 means "no content"
            return JsonResponse({"message": "Bot deleted successfully."}, status=204)
        except Bot.DoesNotExist:
            return JsonResponse({"error": "Bot not found"}, status=404)
        except Exception as e:
            print(f"Error in BotDetailAPIView DELETE: {e}")
            return JsonResponse({"error": str(e)}, status=500)
