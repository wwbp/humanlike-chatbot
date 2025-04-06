import logging
from locust import HttpUser, task, between
import random
import datetime
from gevent.lock import Semaphore

# Configure logging to file for errors and info
logging.basicConfig(
    filename="locust_errors.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Global dictionary to count failures by key (request type + endpoint)
failure_counts = {}


def log_failure_event(request_type, name, response_time, response_length, exception, status_code):
    key = f"{request_type} {name} [Status: {status_code}]"
    failure_counts[key] = failure_counts.get(key, 0) + 1
    logging.error("Request Failure: %s %s took %.2fms, response_length: %s, status_code: %s. Exception: %s. Count: %d",
                  request_type, name, response_time, response_length, status_code, exception, failure_counts[key])


def log_success_event(request_type, name, response_time, response_length):
    logging.info("Request Success: %s %s took %.2fms, response_length: %s",
                 request_type, name, response_time, response_length)


# Global counter to track completed users in the experiment
completed_users = 0
completed_lock = Semaphore()


class ConversationUser(HttpUser):
    wait_time = between(1, 3)
    # Number of chat messages per conversation (adjustable)
    conversation_length = 10

    # Payload templates for initialization and chat messages
    payloads = {
        "initialize": {
            "initial_utterance": "Hello!",
            "study_name": "study1",
            "user_group": "group1",
            "survey_id": "survey1",
            "survey_meta_data": "meta"
        },
        "chat": {
            "message": "How are you?"
        }
    }

    def fetch_bots(self):
        """Fetch available bots from the /api/bots/ endpoint."""
        response = self.client.get("/api/bots/")
        if response.status_code == 200:
            return response.json().get("bots", [])
        else:
            log_failure_event("GET", "/api/bots/",
                              response.elapsed.total_seconds() * 1000,
                              len(response.content),
                              Exception("Failed to fetch bots"),
                              response.status_code)
            return []

    def initialize_conversation(self, bot_name, participant_id):
        """Initialize a conversation via /api/initialize_conversation/."""
        # Generate a unique conversation_id for the payload
        conv_id_generated = f"conv_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        init_payload = self.payloads["initialize"].copy()
        init_payload.update({
            "bot_name": bot_name,
            "participant_id": participant_id,
            "conversation_id": conv_id_generated
        })
        response = self.client.post(
            "/api/initialize_conversation/", json=init_payload)
        if response.status_code == 200:
            return response.json().get("conversation_id")
        else:
            log_failure_event("POST", "/api/initialize_conversation/",
                              response.elapsed.total_seconds() * 1000,
                              len(response.content),
                              Exception("Conversation initialization failed"),
                              response.status_code)
            return None

    def send_chat_message(self, bot_name, conversation_id, participant_id, message):
        """Send a chat message via /api/chatbot/ and capture the response."""
        chat_payload = self.payloads["chat"].copy()
        chat_payload.update({
            "message": message,
            "bot_name": bot_name,
            "conversation_id": conversation_id,
            "participant_id": participant_id
        })
        response = self.client.post("/api/chatbot/", json=chat_payload)
        if response.status_code != 200:
            log_failure_event("POST", "/api/chatbot/",
                              response.elapsed.total_seconds() * 1000,
                              len(response.content),
                              Exception("Chat message failed"),
                              response.status_code)
        else:
            log_success_event("POST", "/api/chatbot/",
                              response.elapsed.total_seconds() * 1000,
                              len(response.content))
        return response

    @task
    def conversation_flow(self):
        """
        Simulates a full conversation:
          1. Fetch bots and select one.
          2. Initialize conversation.
          3. Send a configurable number of chat messages.
          4. Stop further tasks for this user.
        """
        participant_id = f"test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

        # Step 1: Fetch bots and select one at random
        bots = self.fetch_bots()
        if not bots:
            logging.error("No bots available for conversation.")
            return
        bot = random.choice(bots)
        bot_name = bot.get("name")

        # Step 2: Initialize conversation
        conversation_id = self.initialize_conversation(
            bot_name, participant_id)
        if not conversation_id:
            logging.error(
                "Failed to initialize conversation for bot: %s", bot_name)
            return

        # Step 3: Simulate conversation with a set number of messages
        for i in range(self.conversation_length):
            message = f"Message {i+1}: How are you?"
            self.send_chat_message(
                bot_name, conversation_id, participant_id, message)

        # Log conversation completion
        log_success_event("INFO", "Conversation Complete", 0, 0)
        logging.info(
            "Conversation completed for participant %s with bot %s", participant_id, bot_name)
        self.interrupt()

    def on_stop(self):
        """
        Called when a simulated user stops.
        Increments the global counter, and if all users have finished,
        stops the locust test runner.
        """
        global completed_users
        with completed_lock:
            completed_users += 1
            total_users = self.environment.runner.user_count
            logging.info(
                "User completed conversation. Total completed: %d/%d", completed_users, total_users)
            if completed_users >= total_users:
                logging.info(
                    "All users have completed their conversation. Stopping test.")
                self.environment.runner.quit()
