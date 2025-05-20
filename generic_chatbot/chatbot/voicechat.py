import os
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.core.files.storage import default_storage
from .models import Conversation, Utterance 

@csrf_exempt
@require_GET
def get_realtime_session(request):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "gpt-4o-realtime-preview-2024-12-17",
        "voice": "alloy",  # change voice if needed
    }

    try:
        response = requests.post("https://api.openai.com/v1/realtime/sessions", headers=headers, json=data)
        return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        print(f"[DEBUG] Error fetching realtime session: {e}")
        return JsonResponse({"error": "Failed to get session from OpenAI"}, status=500)

@csrf_exempt
@require_POST
def upload_voice_utterance(request):
    try:
        print("✅✅✅✅✅✅✅✅")
        audio_file = request.FILES.get("audio")
        transcript = request.POST.get("transcript", "")
        conversation_id = request.POST.get("conversation_id")
        participant_id = request.POST.get("participant_id")
        bot_name = request.POST.get("bot_name")
        is_model = request.POST.get("is_model", "").lower() == "true"

        if not conversation_id or not bot_name:
            return JsonResponse({"error": "Missing conversation_id or bot_name."}, status=400)

        if not transcript and not audio_file:
            return JsonResponse({"error": "Must include either transcript or audio."}, status=400)

        conversation = Conversation.objects.get(conversation_id=conversation_id)

        speaker_id = "assistant" if is_model else "participant"

        utterance = Utterance.objects.create(
            conversation=conversation,
            speaker_id=speaker_id,
            bot_name=bot_name,
            participant_id=participant_id,
            text=transcript,
            audio_file=audio_file if not is_model else None,
            is_voice=bool(audio_file),
        )

        print(f"✅ Saved {'model' if is_model else 'user'} utterance:", utterance.text[:50])
        return JsonResponse({"message": "Saved successfully", "id": utterance.id})

    except Conversation.DoesNotExist:
        print(f"[ERROR] Conversation ID '{conversation_id}' not found.")
        return JsonResponse({"error": "Conversation not found."}, status=404)
    except Exception as e:
        print(f"[ERROR] Failed to save voice/text utterance: {e}")
        return JsonResponse({"error": "Failed to save utterance"}, status=500)
