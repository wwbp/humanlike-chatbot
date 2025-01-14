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
