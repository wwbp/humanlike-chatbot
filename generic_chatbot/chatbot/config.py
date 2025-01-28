import json
from django.db import connection
from django.apps import apps


def load_config():
    """
    Load the configuration from config.json and save bots to the database.
    """
    try:
        # Load the JSON file
        with open("config.json", "r") as file:
            config = json.load(file)

        # Check if "bots" exists in the configuration
        bots = config.get("bots", [])
        if not bots:
            print("No bots found in configuration.")
            return config

        # Check if the database is ready
        if not connection.introspection.table_names():
            print("Database not ready. Skipping bot loading.")
            return config

        # Dynamically fetch the Bot model
        Bot = apps.get_model("chatbot", "Bot")  # Replace "chatbot" with your app name

        # Save or update bots in the database
        for bot in bots:
            Bot.objects.update_or_create(
                name=bot["name"], defaults={"prompt": bot["prompt"]}
            )
        print("Bots loaded successfully.")

        return config
    except FileNotFoundError:
        raise RuntimeError("Configuration file 'config.json' not found.")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding 'config.json': {e}")
    except Exception as e:
        print(f"Unexpected error loading config: {e}")
        raise
