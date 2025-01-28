from django.urls import path
from .views import ChatbotAPIView, ListBotsAPIView, health_check, InitializeConversationAPIView

urlpatterns = [
    path("api/initialize_conversation/", InitializeConversationAPIView.as_view(), name="initialize_conversation"),
    path('api/chatbot/', ChatbotAPIView.as_view(), name='chatbot_api'),
    path('api/bots/', ListBotsAPIView.as_view(), name='list_bots'),
    path('health/', health_check, name='health_check'),
]
