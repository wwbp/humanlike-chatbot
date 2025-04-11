from django.contrib import admin

"""
from django.db import models

class Conversation(models.Model):
    conversation_id = models.CharField(max_length=255, unique=True)  # Conversation ID
    bot_name = models.CharField(max_length=255, default ="DefaultBot") # Bot Name
    participant_id = models.CharField(max_length=255)
    initial_utterance = models.CharField(max_length=255, null=True, blank=True)
    study_name = models.CharField(max_length=255, null=True, blank=True)
    user_group = models.CharField(max_length=255, null=True, blank=True)
    survey_id = models.CharField(max_length=255, null=True, blank=True)  # Survey ID
    survey_meta_data = models.TextField(null=True, blank=True)  # Survey metadata (can be long)
    started_time = models.DateTimeField(auto_now_add=True)  # Start time

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
    name = models.CharField(max_length=255, unique=True, default="DefaultBotName")  # Make name the unique identifier
    prompt = models.TextField()  # Bot's prompt
    model_type = models.CharField(max_length=255, default="OpenAI")  # Model type (e.g., OpenAI, Anthropic)
    model_id = models.CharField(max_length=255, default="gpt-4")  # Model ID, optional
    initial_utterance = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name

class Keystroke(models.Model):
    conversation_id = models.CharField(max_length=255)  # Respnose_ID but not FK to conversation because keystroke logging can happen without conversation registration
    total_time_on_page = models.FloatField()
    total_time_away_from_page = models.FloatField()
    keystroke_count = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=False)

    def __str__(self):
        return f"Keystroke log for conversation {self.conversation_id} at {self.timestamp}"

"""

from .models import Conversation, Bot, Utterance, Keystroke
# Register your models here.
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('conversation_id', 'bot_name', 'participant_id', 'initial_utterance', 'started_time')
    search_fields = ('conversation_id', 'bot_name', 'participant_id')
    list_filter = ('bot_name', 'started_time')
    ordering = ('-started_time',)
    date_hierarchy = 'started_time'
    list_per_page = 20

@admin.register(Utterance)
class UtteranceAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'speaker_id', 'created_time', 'text')
    search_fields = ('conversation__conversation_id', 'speaker_id', 'text')
    list_filter = ('speaker_id', 'created_time')
    ordering = ('-created_time',)
    date_hierarchy = 'created_time'
    list_per_page = 20

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_type', 'model_id', 'initial_utterance')
    search_fields = ('name', 'model_type', 'model_id')
    list_filter = ('model_type',)
    ordering = ('name',)
    list_per_page = 20

@admin.register(Keystroke)
class KeystrokeAdmin(admin.ModelAdmin):
    list_display = ('conversation_id', 'total_time_on_page', 'total_time_away_from_page', 'keystroke_count', 'timestamp')
    search_fields = ('conversation_id',)
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    list_per_page = 20

