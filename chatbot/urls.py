from django.urls import path
from . import views

urlpatterns = [
    
    path("chatbot/", views.chatbot_view, name="chatbot_view"),
    # path("chat/", views.chat, name="chat_page"),

]