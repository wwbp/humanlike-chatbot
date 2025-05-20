import os
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


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
