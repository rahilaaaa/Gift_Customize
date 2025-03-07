from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats")
    message = models.TextField(verbose_name="Message")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="Role")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")

    def __str__(self):
        return f"{self.user.username} - {self.role}: {self.message[:50]}"
