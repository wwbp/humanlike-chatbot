from django.db import models

class Conversation(models.Model):
    conversation_id = models.CharField(max_length=255, unique=True)  # Conversation ID
    bot_name = models.CharField(max_length=255, default ="DefaultBot") # Bot Name
    participant_id = models.CharField(max_length=255)
    prompt = models.CharField(max_length=255, null=True, blank=True)
    study_name = models.CharField(max_length=255, null=True, blank=True)
    user_group = models.CharField(max_length=255, null=True, blank=True)               
    started_time = models.DateTimeField(auto_now_add=True)          # Start time

    def __str__(self):
        return f"Conversation {self.conversation_id} started at {self.started_time}"

class Utterance(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="utterances",null=True, blank=True)   # Unique identifier per conversation
    speaker_id = models.CharField(max_length=255)       # 'participant' or 'bot'
    bot_name = models.CharField(max_length=255,null=True, blank=True)  
    participant_id = models.CharField(max_length=255,null=True, blank=True)  
    created_time = models.DateTimeField(auto_now_add=True)               # Timestamp
    text = models.TextField()      

    def __str__(self):
        return f"{self.speaker_id}: {self.text[:50]}"


class Bot(models.Model):
    name = models.CharField(max_length=255, default="DefaultBotName")  # Make name the unique identifier
    prompt = models.TextField()  # Bot's prompt

    def __str__(self):
        return self.name
