from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json, logging
from .models import Conversation

# Configure logging
logger = logging.getLogger(__name__)

@csrf_exempt  # Disable CSRF for testing; use authentication in production
def update_keystrokes(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            conversation_id = data.get("conversation_id")
            total_time_on_page = data.get("total_time_on_page")
            total_time_away_from_page = data.get("total_time_away_from_page")
            keystroke_count = data.get("keystroke_count")

            print(f"conversation_id: {conversation_id} \n total_time_on_page: { total_time_on_page} \n total_time_away_from_page: {total_time_away_from_page} \n keystroke_count: {keystroke_count} ")

            ''' 
            if not conversation_id:
                return JsonResponse({"error": "conversation_id is required"}, status=400)

            # Find the conversation instance
            try:
                conversation = Conversation.objects.get(conversation_id=conversation_id)
            except Conversation.DoesNotExist:
                return JsonResponse({"error": "Conversation not found"}, status=404)
            
            # Ensure values are not None before updating
            if total_time_on_page is not None:
                conversation.total_time_on_page = total_time_on_page
            if total_time_away_from_page is not None:
                conversation.total_time_away_from_page = total_time_away_from_page
            if keystroke_count is not None:
                conversation.keystroke_count = keystroke_count
            
            conversation.save()
        '''
            return JsonResponse({"message": "Keystroke data saved successfully"}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
 
    return JsonResponse({"error": "Invalid request method"}, status=405)
