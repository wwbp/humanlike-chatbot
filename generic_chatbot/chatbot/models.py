from django.db import models

class Chat(models.Model):
    conversation_id = models.CharField(max_length=255, default="default_conversation")
    speaker_id = models.CharField(max_length=255, default="unknown")
    text = models.TextField()
    bot_name = models.CharField(max_length=255, blank=True, null=True)  
    bot_prompt = models.TextField(blank=True, null=True)  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.speaker_id}: {self.text[:50]}"

class Utterance(models.Model):
    conversation_id = models.CharField(max_length=255)  # Unique identifier per conversation
    speaker_id = models.CharField(max_length=255)       # 'user' or 'assistant'
    bot_name = models.CharField(max_length=255, blank=True, null=True)  # Bot's name
    qualtrics_id = models.CharField(max_length=255, blank=True, null=True)  # Optional Qualtrics ID
    created_time = models.DateTimeField(auto_now_add=True)               # Timestamp
    text = models.TextField()      

    def __str__(self):
        return f"{self.speaker_id}: {self.text[:50]}"

class Conversation(models.Model):
    conversation_id = models.CharField(max_length=255, unique=True)  # Conversation ID
    bot_id = models.CharField(max_length=255)                       # Bot ID
    human_id = models.CharField(max_length=255)                     # Human ID
    started_time = models.DateTimeField(auto_now_add=True)          # Start time

    def __str__(self):
        return f"Conversation {self.conversation_id} started at {self.started_time}"


class Bot(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Make name the unique identifier
    prompt = models.TextField()  # Bot's prompt

    def __str__(self):
        return self.name
