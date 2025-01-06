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
from accounts.models import Chat
from asgiref.sync import sync_to_async
import json


def csrf(request):
    csrf_token = get_token(request)  # Fetch the CSRF token
    return JsonResponse({'csrfToken': csrf_token})

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
async def save_chat_to_db(conversation_id, speaker_id, text):
    try:
        await sync_to_async(Chat.objects.create)(
            conversation_id=conversation_id,
            speaker_id=speaker_id,
            text=text
        )
        print(f"Successfully saved {speaker_id}'s message to the database.")
    except Exception as e:
        print(f"Failed to save message to the database: {e}")

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(View):
    async def post(self, request, *args, **kwargs):
        try:
            # Parse JSON payload
            data = json.loads(request.body)
            message = data.get('message', '')
            bot_name = data.get('bot_name', bots[0]["name"] if bots else "DefaultBot")

            # Find the bot
            selected_bot = next((bot for bot in bots if bot["name"] == bot_name), None)
            if not selected_bot:
                return JsonResponse({'error': 'Bot not found.'}, status=400)

            kani = Kani(engine, system_prompt=selected_bot["prompt"])
            # Process bot response asynchronously
            response = await kani.chat_round(message)
            response_text = response.text

            # Save chat asynchronously
            await sync_to_async(Chat.objects.create)(
                conversation_id="conversation_1",
                speaker_id="user",
                text=message
            )
            await sync_to_async(Chat.objects.create)(
                conversation_id="conversation_1",
                speaker_id="assistant",
                text=response_text
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