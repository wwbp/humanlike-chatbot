import json
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Bot

@method_decorator(csrf_exempt, name='dispatch')
class ListBotsAPIView(View):
    """
    GET  -> List all bots
    POST -> Create a new bot
    """

    def get(self, request, *args, **kwargs):
        try:
            # Return all bots as a list of dicts
            bots = Bot.objects.values("id", "name", "model_type", "model_id", "prompt")
            return JsonResponse({"bots": list(bots)}, status=200)
        except Exception as e:
            print(f"Error in ListBotsAPIView GET: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def post(self, request, *args, **kwargs):
        """
        Create a new Bot in the database.
        Expects JSON body like:
        {
          "name": "MyBot",
          "model_type": "OpenAI",
          "model_id": "gpt-4",
          "prompt": "..."
        }
        """
        try:
            data = json.loads(request.body)
            name = data.get("name")
            model_type = data.get("model_type")
            model_id = data.get("model_id")
            prompt = data.get("prompt", "")

            # Minimal validation
            if not name or not model_type or not model_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Create and save a new Bot
            bot = Bot.objects.create(
                name=name,
                model_type=model_type,
                model_id=model_id,
                prompt=prompt
            )

            return JsonResponse(
                {
                    "id": bot.id,
                    "name": bot.name,
                    "model_type": bot.model_type,
                    "model_id": bot.model_id,
                    "prompt": bot.prompt,
                },
                status=201
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except Exception as e:
            print(f"Error in ListBotsAPIView POST: {e}")
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BotDetailAPIView(View):
    """
    GET    -> Retrieve single bot by ID (optional, if your front-end ever needs it)
    PUT    -> Update an existing bot by ID
    DELETE -> Delete a bot by ID
    """

    def get(self, request, pk, *args, **kwargs):
        """Optional: get a single bot's details by ID."""
        try:
            bot = Bot.objects.get(pk=pk)
            data = {
                "id": bot.id,
                "name": bot.name,
                "model_type": bot.model_type,
                "model_id": bot.model_id,
                "prompt": bot.prompt,
            }
            return JsonResponse(data, status=200)
        except Bot.DoesNotExist:
            return JsonResponse({"error": "Bot not found"}, status=404)
        except Exception as e:
            print(f"Error in BotDetailAPIView GET: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def put(self, request, pk, *args, **kwargs):
        """Update an existing bot by ID."""
        try:
            bot = Bot.objects.get(pk=pk)
        except Bot.DoesNotExist:
            return JsonResponse({"error": "Bot not found"}, status=404)

        try:
            data = json.loads(request.body)
            bot.name = data.get("name", bot.name)
            bot.model_type = data.get("model_type", bot.model_type)
            bot.model_id = data.get("model_id", bot.model_id)
            bot.prompt = data.get("prompt", bot.prompt)
            bot.save()

            return JsonResponse({"message": "Bot updated successfully."}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except Exception as e:
            print(f"Error in BotDetailAPIView PUT: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def delete(self, request, pk, *args, **kwargs):
        """Delete an existing bot by ID."""
        try:
            bot = Bot.objects.get(pk=pk)
            bot.delete()
            # 204 means "no content"
            return JsonResponse({"message": "Bot deleted successfully."}, status=204)
        except Bot.DoesNotExist:
            return JsonResponse({"error": "Bot not found"}, status=404)
        except Exception as e:
            print(f"Error in BotDetailAPIView DELETE: {e}")
            return JsonResponse({"error": str(e)}, status=500)