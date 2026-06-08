import logging
import os

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from ..models import Conversation, Utterance

logger = logging.getLogger(__name__)

_ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/ogg",
    "audio/ogg;codecs=opus",
    "audio/wav",
    "audio/mpeg",
    "audio/mp4",
}


@csrf_exempt
@require_GET
def get_realtime_session(request):
    conversation_id = request.GET.get("conversation_id")
    if not conversation_id:
        return JsonResponse({"error": "Missing conversation_id."}, status=400)

    if not Conversation.objects.filter(conversation_id=conversation_id).exists():
        return JsonResponse({"error": "Conversation not found."}, status=404)

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set; cannot create realtime session")
        return JsonResponse(
            {"error": "Voice service is not available."},
            status=503,
        )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "gpt-4o-realtime-preview-2024-12-17",
        "voice": "alloy",
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/realtime/sessions",
            headers=headers,
            json=data,
        )
        return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        logger.error(f"Error fetching realtime session: {e}")
        return JsonResponse({"error": "Failed to get session from OpenAI"}, status=500)


@csrf_exempt
@require_POST
def upload_voice_utterance(request):
    try:
        audio_file = request.FILES.get("audio")
        transcript = request.POST.get("transcript", "")
        conversation_id = request.POST.get("conversation_id")
        participant_id = request.POST.get("participant_id")
        bot_name = request.POST.get("bot_name")
        is_voice = request.POST.get("is_voice", "").lower() == "true"

        if not conversation_id:
            return JsonResponse({"error": "Missing conversation_id."}, status=400)

        if not transcript and not audio_file:
            return JsonResponse(
                {"error": "Must include either transcript or audio."},
                status=400,
            )

        if audio_file:
            mime = audio_file.content_type.split(";")[0].strip()
            if (
                f"{mime}" not in _ALLOWED_AUDIO_MIME_TYPES
                and audio_file.content_type not in _ALLOWED_AUDIO_MIME_TYPES
            ):
                return JsonResponse({"error": "Unsupported audio format."}, status=415)

        conversation = Conversation.objects.get(conversation_id=conversation_id)

        speaker_id = "assistant" if bot_name else "participant"

        utterance = Utterance.objects.create(
            conversation=conversation,
            speaker_id=speaker_id,
            bot_name=bot_name if speaker_id == "assistant" else None,
            participant_id=participant_id if speaker_id == "participant" else None,
            text=transcript,
            audio_file=audio_file,
            is_voice=is_voice,
        )
        return JsonResponse({"message": "Saved successfully", "id": utterance.id})

    except Conversation.DoesNotExist:
        logger.error(f"Conversation ID '{conversation_id}' not found.")
        return JsonResponse({"error": "Conversation not found."}, status=404)
    except Exception as e:
        logger.error(f"Failed to save voice/text utterance: {e}")
        return JsonResponse({"error": "Failed to save utterance"}, status=500)
