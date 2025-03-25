import json
from datetime import datetime
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from asgiref.sync import async_to_sync
from .models import Conversation, Bot
from .runchat import save_chat_to_db 

@method_decorator(csrf_exempt, name='dispatch')
class InitializeConversationAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            print("[DEBUG] Entering InitializeConversationAPIView.post()...")

            try:
                data = json.loads(request.body)
            except Exception as parse_error:
                print(f"[DEBUG] JSON parse error: {parse_error}")
                return JsonResponse({"error": "Invalid JSON in request body."}, status=400)

            print(f"[DEBUG] Received JSON data: {data}")

            conversation_id = data.get("conversation_id")
            bot_name = data.get("bot_name")
            participant_id = data.get("participant_id")
            study_name = data.get("study_name", "n/a")
            user_group = data.get("user_group", "n/a")
            survey_id = data.get("survey_id", "n/a")
            survey_meta_data = json.dumps(data)

            if not bot_name or not conversation_id:
                return JsonResponse(
                    {"error": "Both 'bot_name' and 'conversation_id' are required."}, 
                    status=400
                )

            try:
                bot = Bot.objects.get(name=bot_name)
                print(f"[DEBUG] Found bot: {bot_name}")
            except Bot.DoesNotExist:
                return JsonResponse({"error": f"No bot found with the name '{bot_name}'."}, status=404)
            except Exception as bot_fetch_error:
                print(f"[DEBUG] Error fetching bot: {bot_fetch_error}")
                return JsonResponse({"error": "Error fetching the bot from the database."}, status=500)

            # Save conversation
            try:
                Conversation.objects.create(
                    conversation_id=conversation_id,
                    bot_name=bot.name,
                    participant_id=participant_id,
                    initial_utterance=bot.initial_utterance,
                    study_name=study_name,
                    user_group=user_group,
                    survey_id=survey_id,
                    survey_meta_data=survey_meta_data,
                    started_time=datetime.now(),
                )
                print("[DEBUG] Conversation created.")
            except Exception as create_conv_error:
                print(f"[DEBUG] Error creating Conversation: {create_conv_error}")
                return JsonResponse({"error": "Failed to create Conversation."}, status=500)

            # ✅ Save bot's initial utterance as an assistant message
            if bot.initial_utterance and bot.initial_utterance.strip():
                try:
                    async_to_sync(save_chat_to_db)(
                        conversation_id=conversation_id,
                        speaker_id="assistant",
                        text=bot.initial_utterance.strip(),
                        bot_name=bot.name,
                        participant_id=None
                    )
                    print("[DEBUG] Initial bot message saved to DB.")
                except Exception as save_error:
                    print(f"[DEBUG] Failed to save initial bot message: {save_error}")

            return JsonResponse({
                "conversation_id": conversation_id,
                "message": "Conversation initialized successfully.",
                "initial_utterance": bot.initial_utterance or ""
            }, status=200)

        except Exception as e:
            print(f"[DEBUG] Unhandled exception in InitializeConversationAPIView: {e}")
            return JsonResponse({"error": "Unexpected error occurred."}, status=500)
