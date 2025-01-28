from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot"

    def ready(self):
        """
        Called when the app is ready. Loads the configuration and saves bots to the database.
        """
        try:
            load_config()
        except Exception as e:
            print(f"Error loading bots during app initialization: {e}")