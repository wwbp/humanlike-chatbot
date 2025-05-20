from django.urls import path
from .views import ChatbotAPIView, health_check, get_realtime_session 
from .bots import ListBotsAPIView, BotDetailAPIView  # Import from bots.py
from .conversation import InitializeConversationAPIView  # Import from conversation.py
from .keystroke import update_keystrokes

urlpatterns = [
    # 1) Health Check
    path('health/', health_check, name='health_check'),

    # 2) Initialize a Conversation
    path("api/initialize_conversation/", InitializeConversationAPIView.as_view(), name="initialize_conversation"),

    # 3) Chatbot Conversation Endpoint
    path('api/chatbot/', ChatbotAPIView.as_view(), name='chatbot_api'),

    # 4) Bots Collection (List and/or Create)
    path('api/bots/', ListBotsAPIView.as_view(), name='list_bots'),

    # 5) Bot Detail by Primary Key (Retrieve, Update, Delete)
    path('api/bots/<int:pk>/', BotDetailAPIView.as_view(), name='bot-detail'),

    # 6) update keystrokes 
    path('api/update_keystrokes/', update_keystrokes, name = 'update_keystrokes'),

    # 7) get realtime sesion
    path("api/session/", get_realtime_session, name="get_realtime_session"),
]
