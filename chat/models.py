from django.db import models
from user_management.models import User


class DirectChat(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver')
    created_time = models.DateTimeField(auto_now_add=True)
    chat_room_id = models.CharField(max_length=255, default=1)

    def __str__(self):
        return self.created_time


class DirectChatMessage(models.Model):
    direct_chat = models.ForeignKey(DirectChat, on_delete=models.CASCADE)
    chat_message = models.CharField(max_length=255, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_by', default=1)

    def __str__(self):
        return self.chat_message


class DirectChatMessageReply(models.Model):
    direct_chat_message = models.ForeignKey(DirectChatMessage, on_delete=models.CASCADE)
    message_reply = models.CharField(max_length=255, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message_reply
