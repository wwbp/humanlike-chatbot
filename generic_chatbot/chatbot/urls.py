from django.urls import path
from .views import ChatbotAPIView, ListBotsAPIView

urlpatterns = [
    path('api/chatbot/', ChatbotAPIView.as_view(), name='chatbot_api'),
    path('api/bots/', ListBotsAPIView.as_view(), name='list_bots'),
]
