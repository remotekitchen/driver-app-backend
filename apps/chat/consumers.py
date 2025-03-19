import json
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from .models import ChatMessage
from channels.layers import get_channel_layer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_layer = get_channel_layer()
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.chat_group = f'chat_{self.order_id}'

        # Authenticate the consumer using Chatchef API
        self.user = await self.authenticate_user()

        if self.user:
            # Add the user to the chat group
            await self.channel_layer.group_add(self.chat_group, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender = self.user['id']

        # Save message in the database
        chat_message = ChatMessage.objects.create(
            order_id=self.order_id, sender_id=sender, message=message
        )

        # Broadcast the message
        await self.channel_layer.group_send(
            self.chat_group,
            {
                "type": "chat.message",
                "message": message,
                "sender": sender,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def authenticate_user(self):
        """ Authenticate user by calling the Chatchef backend API """
        headers = dict(self.scope['headers'])
        auth_header = headers.get(b'authorization')

        if not auth_header:
            return None

        token = auth_header.decode().split(" ")[1]  # Extract the token

        try:
            response = requests.get(
                f"{settings.CHATCHEF_BACKEND_URL}accounts/v1/user/verify-chat-user/",
                headers={"Authorization": f"Token {token}"}
            )
            if response.status_code == 200:
                return response.json()  # Return user data
        except requests.exceptions.RequestException:
            return None

        return None