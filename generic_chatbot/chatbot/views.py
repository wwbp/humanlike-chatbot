import json
from django.shortcuts import render
from django.http import JsonResponse
from kani import Kani
from server.engine import initialize_engine
from .models import Chat
from asgiref.sync import sync_to_async

# Load config.json
def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise RuntimeError("Configuration file 'config.json' not found.")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding 'config.json': {e}")

# Initialize engine and bot dynamically
config = load_config()
default_model_config = config["default_model_config"]
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

# Chatbot view
# Chatbot view
async def chatbot(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        bot_name = request.POST.get('bot_name', bots[0]["name"])  # Default to the first bot
        selected_bot = next((bot for bot in bots if bot["name"] == bot_name), bots[0])

        kani = Kani(engine, system_prompt=selected_bot["prompt"])

        try:
            response = await kani.chat_round(message)
            print(f"Bot response: {response.text}")

            # Save user message to MariaDB
            await save_chat_to_db("conversation_1", "user", message)

            # Save bot response to MariaDB
            await save_chat_to_db("conversation_1", "assistant", response.text)

            return JsonResponse({'message': message, 'response': response.text, 'bot_name': bot_name})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    bot_names = [bot["name"] for bot in bots]
    return render(request, 'chatbot.html', {'bot_names': bot_names, 'app_title': config.get("app_title", "Chatbot")})
