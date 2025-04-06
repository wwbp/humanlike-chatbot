import json
from datetime import datetime
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
from server.engine import get_or_create_engine
from .models import Conversation, Bot

# Dictionary to store per-engine configurations
engine_instances = {}

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
