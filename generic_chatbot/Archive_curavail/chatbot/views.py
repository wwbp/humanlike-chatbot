import json
import sys
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
from datetime import datetime
from django.core.cache import cache
from kani import Kani, ChatMessage, ChatRole
from .models import Conversation, Bot, Utterance
from .bots import ListBotsAPIView, BotDetailAPIView
from .conversation import InitializeConversationAPIView
from server.engine import get_or_create_engine

# Dictionary to store per-engine configurations
engine_instances = {}

def health_check(request):
    return JsonResponse({"status": "ok"})

async def save_chat_to_db(conversation_id, speaker_id, text, bot_name=None, participant_id=None):
    """
    Save chat messages asynchronously to the Utterance table.
    """
    try:
        conversation = await sync_to_async(Conversation.objects.get)(conversation_id=conversation_id)
        print(f"Found conversation {conversation.conversation_id}, inserting message...")

        await sync_to_async(Utterance.objects.create)(
            conversation=conversation,
            speaker_id=speaker_id,
            bot_name=bot_name,
            participant_id=participant_id,
            text=text
        )
        print("✅ Successfully saved message to Utterance table.")

    except Conversation.DoesNotExist:
        print(f"❌ Conversation with ID {conversation_id} not found.")
    except Exception as e:
        print(f"❌ Failed to save message to Utterance table: {e}")

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(View):
    """
    Handles chat interactions with the bot.
    """
    async def post(self, request, *args, **kwargs):
        try:
            # Parse JSON payload
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            bot_name = data.get('bot_name', '').strip()
            conversation_id = data.get('conversation_id', None)
            participant_id = data.get('participant_id', None)

            if not message or not bot_name or not conversation_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch bot using sync_to_async
            bot = await sync_to_async(Bot.objects.get)(name=bot_name)
            print("✅ [DEBUG] Bot fetched successfully.")
            sys.stdout.flush()

            # Retrieve conversation history from cache
            cache_key = f"conversation_cache_{conversation_id}"
            conversation_history = cache.get(cache_key, [])  # Default to empty list
            print(f"✅ [DEBUG] Retrieved conversation history from cache: {conversation_history}")
            sys.stdout.flush()

            # Append new user message
            conversation_history.append({"role": "user", "content": message})
            print(f"✅ [DEBUG] Updated conversation history: {conversation_history}")
            sys.stdout.flush()

        
            # Convert conversation history to Kani's ChatMessage format
            formatted_history = [
                ChatMessage(
                    role=ChatRole.USER if msg["role"] == "user" else ChatRole.ASSISTANT,
                    content=str(msg["content"])  # Ensure content is a string
                )
                for msg in conversation_history
            ]

            print("✅ [DEBUG] Sending conversation history to Kani:")
            for msg in formatted_history:
                print(f"🗣 {msg.role}: {msg.content}")
            sys.stdout.flush()


             # Retrieve or create engine
            engine = get_or_create_engine(bot.model_type, bot.model_id, engine_instances)
            kani = Kani(engine, system_prompt=bot.prompt, chat_history = formatted_history)

            latest_user_message = formatted_history[-1].content
            # Generate responses
            response_text = ""
            async for msg in kani.full_round(query=latest_user_message):
                if hasattr(msg, "text") and isinstance(msg.text, str):
                    response_text += msg.text + " "

            response_text = response_text.strip()

            # Append bot response
            conversation_history.append({"role": "assistant", "content": response_text})

            # Ensure only the last 10 turns are retained
            conversation_history = conversation_history[-10:]

            # Update cache with new history (1-hour expiration)
            cache.set(cache_key, conversation_history, timeout=3600)
            print(f"✅ [DEBUG] Saved updated conversation history to cache: {cache.get(cache_key)}")
            sys.stdout.flush()

            # Save user message to the Utterance table
            await save_chat_to_db(
                conversation_id=conversation_id,
                speaker_id="user",
                text=message,
                bot_name=None,
                participant_id=participant_id
            )

            # Save bot response to the Utterance table
            await save_chat_to_db(
                conversation_id=conversation_id,
                speaker_id="assistant",
                text=response_text,
                bot_name=bot.name,
                participant_id=None
            )

            return JsonResponse({'message': message, 'response': response_text, 'bot_name': bot_name}, status=200)

        except Exception as e:
            print(f"❌ [ERROR] ChatbotAPIView Exception: {e}")
            sys.stdout.flush()
            return JsonResponse({'error': str(e)}, status=500)
