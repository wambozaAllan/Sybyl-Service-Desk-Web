from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import DirectChat, DirectChatMessage
from datetime import datetime
from django.db.models import Q


class ChatConsumer2(AsyncWebsocketConsumer):
    async def connect(self):
        sender = self.scope["user"].pk
        self.client_id = self.scope['url_route']['kwargs']['client_id']

        if DirectChat.objects.filter((Q(sender=self.client_id) & Q(receiver=sender)) | (Q(sender=sender) & Q(receiver=self.client_id))).exists():
            obj1 = DirectChat.objects.filter((Q(sender=self.client_id) & Q(receiver=sender)) | (Q(sender=sender) & Q(receiver=self.client_id))).values('chat_room_id').first()
            self.room_group_name = obj1['chat_room_id']
        else:
            self.room_group_name = 'chatroom_%s' % self.client_id + '_' + str(sender)
            obj = DirectChat(sender_id=sender, receiver_id=self.client_id, chat_room_id=self.room_group_name)
            obj.save()
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Called on connection.
        # To accept the connection call:
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        obj3 = DirectChat.objects.filter(chat_room_id=self.room_group_name).values('id').first()
        direct_chat_id = obj3['id']

        obj4 = DirectChatMessage(chat_message=message, direct_chat_id=direct_chat_id, sent_by_id=self.scope["user"].pk)
        obj4.save()
        created_time = datetime.now()
        msg_id = obj4.id

        # Send message to room group
        await self.channel_layer.group_send(

            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                "id": self.scope["user"].id,
                "fname": self.scope["user"].first_name,
                "lname": self.scope["user"].last_name,
                "username": self.scope["user"].username,
                "created_time": str(created_time),
                "msg_id": msg_id,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': event["username"],
            'fname': event["fname"],
            'lname': event["lname"],
            'uid': event["id"],
            'created_time': event["created_time"],
            'msg_id': event["msg_id"],
        }))
