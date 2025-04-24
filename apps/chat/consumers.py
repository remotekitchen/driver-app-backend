import json
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import httpx
from apps.chat.models import ChatMessage
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"🟢 Incoming WebSocket connection: {self.scope['path']}")
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.chat_group = f'chat_{self.order_id}'

        print(f"🔍 User trying to join chat group: {self.chat_group}")  # Debugging

        # Accept the WebSocket connection first
        await self.accept()
        print("✅ WebSocket connection accepted.")

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"📩 Received data: {data}")  # Debugging

        if "token" in data:  # First message contains token
            self.user = await self.authenticate_user(data["token"])

            if self.user:
                print(f"✅ User {self.user['id']} authenticated in chat {self.chat_group}")
                await self.channel_layer.group_add(self.chat_group, self.channel_name)  # Join chat group
            else:
                print("❌ Authentication failed! Closing connection.")
                await self.close()
            return

        # Ensure the user is authenticated before processing messages
        if not hasattr(self, "user") or not self.user:
            print("❌ User not authenticated! Closing connection.")
            await self.close()
            return

        message = data["message"]
        sender = self.user["id"]
        sender_name = self.user.get("username", "Unknown")

        print(f"📩 Message received: '{message}' from {sender} in {self.chat_group}")

        # 🔹 Save the message in the database
        await self.save_message(order_id=self.order_id, sender_id=sender, sender_name=sender_name, message=message)

        # 🔹 Broadcast the message
        await self.channel_layer.group_send(
            self.chat_group,
            {
                "type": "chat.message",
                "message": message,
                "sender": sender,
                "sender_name": sender_name
            }
        )

    async def save_message(self, order_id, sender_id, sender_name, message):
        """ Save message asynchronously using sync_to_async """
        await sync_to_async(ChatMessage.objects.create)(
            order_id=order_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message=message
        )
        print(f"💾 Message saved: {message} from {sender_name}")

    async def chat_message(self, event):
        print(f"📢 Broadcasting message: {event}")  # Debugging line
        await self.send(text_data=json.dumps(event))

    async def authenticate_user(self, token):
        """ Authenticate users from their respective backends asynchronously """

        if "driver" in self.scope["path"]:  # If it's a driver, use the Delivery backend
            auth_url = f"{settings.DELIVERY_BACKEND_URL}auth/api/v1/user/verify-chat-user/"
        else:  # If it's a consumer, use the Chatchef backend
            auth_url = f"{settings.CHATCHEF_BACKEND_URL}accounts/v1/user/verify-chat-user/"

        print(f"🔍 Authenticating user via: {auth_url}")  # Debugging line

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    auth_url,
                    headers={"Authorization": f"Token {token}"},
                    timeout=10  # Avoid hanging forever
                )

                print(f"🔍 Auth API Response Code: {response.status_code}")  # Debugging
                print(f"🔍 Auth API Response Text: {response.text}")  # Debugging

                if response.status_code == 200:
                    print(f"✅ Authentication successful for token: {token}")
                    return response.json()  # Return user data
                else:
                    print(f"❌ Authentication failed: {response.status_code} {response.text}")
            except httpx.RequestError as e:
                print(f"❌ Error connecting to authentication API: {str(e)}")

        return None