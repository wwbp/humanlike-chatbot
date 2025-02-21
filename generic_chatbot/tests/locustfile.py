from locust import HttpUser, task, between
import random
import datetime


class ConversationUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def conversation_flow(self):
        # Generate a unique participant ID
        participant_id = f"test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

        # Retrieve the list of available bots
        bots_response = self.client.get("/api/bots/")
        if bots_response.status_code != 200:
            return  # Abort if unable to fetch bots

        bots = bots_response.json().get("bots", [])
        if not bots:
            return  # Abort if no bots are available

        # Randomly select one bot
        bot = random.choice(bots)
        bot_name = bot.get("name")

        # Step 1: Initialize conversation with the randomly chosen bot and new user
        init_payload = {
            "bot_name": bot_name,
            "participant_id": participant_id,
            "initial_utterance": "Hello!",
            "study_name": "study1",
            "user_group": "group1",
            "survey_id": "survey1",
            "survey_meta_data": "meta"
        }
        init_response = self.client.post(
            "/api/initialize_conversation/", json=init_payload)
        if init_response.status_code != 200:
            return  # Abort if conversation initialization fails

        conversation_id = init_response.json().get("conversation_id")
        if not conversation_id:
            return

        # Step 2: Send a chat message
        chat_payload = {
            "message": "How are you?",
            "bot_name": bot_name,
            "conversation_id": conversation_id,
            "participant_id": participant_id
        }
        self.client.post("/api/chatbot/", json=chat_payload)
