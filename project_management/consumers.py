from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import ProjectForum, ProjectForumMessages, ProjectTeamMember, ProjectForumMessageReplies
from datetime import datetime


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_state = self.scope['url_route']['kwargs']['chatstate']
        self.project_forum_id = self.scope['url_route']['kwargs']['project_forum_id']
        self.msg_id = self.scope['url_route']['kwargs']['msg_id']

        group_name = ProjectForum.objects.filter(id=self.project_forum_id).values('chat_room_id', 'id').first()
        if group_name['chat_room_id'] is None:
            self.room_group_name = 'group_chat_%s' % str(group_name['id'])
            ProjectForum.objects.filter(id=self.project_forum_id).update(chat_room_id=self.room_group_name)
        else:
            self.room_group_name = group_name['chat_room_id']

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

        if int(self.chat_state) is int(0):
            obj5 = ProjectTeamMember.objects.filter(member_id=self.scope["user"].pk).values('id').first()
            project_team_member_id = obj5['id']

            obj4 = ProjectForumMessages(chat_message=message, projectforum_id=self.project_forum_id, team_member_id=project_team_member_id)
            obj4.save()
            created_time = datetime.now()
            msg_id = obj4.id

            # Send message to room group
            await self.channel_layer.group_send(

                self.room_group_name,
                {
                    'type': 'chat_message2',
                    'message': message,
                    "id": self.scope["user"].id,
                    "fname": self.scope["user"].first_name,
                    "lname": self.scope["user"].last_name,
                    "username": self.scope["user"].username,
                    "created_time": str(created_time),
                    "msg_id": msg_id,
                }
            )
        else:
            obj55 = ProjectTeamMember.objects.filter(member_id=self.scope["user"].pk).values('id').first()
            project_team_member_id = obj55['id']

            obj44 = ProjectForumMessageReplies(reply=message, projectforummessage_id=self.msg_id, team_member_id=project_team_member_id)
            obj44.save()
            reply_id = obj44.id
            created_time = datetime.now()

            # Send message to room group
            await self.channel_layer.group_send(

                self.room_group_name,
                {
                    'type': 'chat_replies',
                    'message': message,
                    "id": self.scope["user"].id,
                    "fname": self.scope["user"].first_name,
                    "lname": self.scope["user"].last_name,
                    "username": self.scope["user"].username,
                    "created_time": str(created_time),
                    "reply_id": reply_id,
                }
            )

    # Receive message from room group
    async def chat_message2(self, event):
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

    # Receive message from room group
    async def chat_replies(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': event["username"],
            'fname': event["fname"],
            'lname': event["lname"],
            'uid': event["id"],
            'created_time': event["created_time"],
            'reply_id': event["reply_id"],
        }))
