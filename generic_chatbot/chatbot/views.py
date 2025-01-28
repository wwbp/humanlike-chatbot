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
from .models import Chat, Bot, Utterance
import json

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
bots = config.get("bots", [])

#save chat
async def save_chat_to_db(conversation_id, speaker_id, text, bot_name=None, qualtrics_id=None):
    try:
        await sync_to_async(Utterance.objects.create)(
            conversation_id=conversation_id,
            speaker_id=speaker_id,
            text=text,
            bot_name=bot_name,
            qualtrics_id=qualtrics_id
        )
        print(f"Successfully saved {speaker_id}'s message to the Utterance table.")
    except Exception as e:
        print(f"Failed to save message to the Utterance table: {e}")


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(View):
    async def post(self, request, *args, **kwargs):
        try:
            # Parse JSON payload
            data = json.loads(request.body)
            message = data.get('message', '')
            bot_name = data.get('bot_name', bots[0]["name"] if bots else "DefaultBot")
            conversation_id = data.get('conversation_id', None)  
            qualtrics_id = data.get('qualtrics_id', None)  # Optional Qualtrics ID

            # Generate a conversation ID if missing
            if not conversation_id:
                import uuid
                conversation_id = str(uuid.uuid4())  # Temporary ID until Qualtrics integration

            # Find the bot
            selected_bot = next((bot for bot in bots if bot["name"] == bot_name), None)
            if not selected_bot:
                return JsonResponse({'error': 'Bot not found.'}, status=400)

            kani = Kani(engine, system_prompt=selected_bot["prompt"])
            # Process bot response asynchronously
            response = await kani.chat_round(message)
            response_text = response.text

            # Save user message to the Utterance table
            await save_chat_to_db(
                conversation_id=conversation_id,
                speaker_id="user",
                text=message,
                bot_name=None,  # User message, no bot name
                qualtrics_id=qualtrics_id
            )

            # Save bot response to the Utterance table
            await save_chat_to_db(
                conversation_id=conversation_id,
                speaker_id="assistant",
                text=response_text,
                bot_name=selected_bot["name"],  # Bot's name
                qualtrics_id=None
            )

            # Return the bot's response
            return JsonResponse({'message': message, 'response': response_text, 'bot_name': bot_name}, status=200)
        except Exception as e:
            print(f"Error in ChatbotAPIView: {e}")
            return JsonResponse({'error': str(e)}, status=500)

class ListBotsAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            if not bots:
                raise ValueError("No bots found in configuration")

            bot_names = [bot['name'] for bot in bots]
            return JsonResponse({'bot_names': bot_names}, status=200)
        except Exception as e:
            print(f"Error in ListBotsAPIView: {e}")
            return JsonResponse({'error': str(e)}, status=500)