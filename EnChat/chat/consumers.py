import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from .models import PrivateMessage
from django.utils import timezone
from utils import encrypt_message, decrypt_message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        self.receiver_id = self.scope["url_route"]["kwargs"].get("receiver_id", None)

        if not self.user.is_authenticated or not self.receiver_id:
            await self.close()
            return

        self.room_name = f"chat_{min(self.user.id, int(self.receiver_id))}_{max(self.user.id, int(self.receiver_id))}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data["message"]
        receiver = await self.get_user(self.receiver_id)

        if receiver:
            msg = await self.save_message(self.user, receiver, message_text)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "chat_message",
                    "message_id": msg.id,
                    "sender": self.user.username,
                    "message": message_text,
                    "timestamp": str(msg.timestamp),
                },
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def read_message(self, text_data):
        data = json.loads(text_data)
        message_id = data["message_id"]
        message = await self.get_message(message_id)

        if message and message.receiver == self.user and not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            await message.asave()
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "read_receipt",
                    "message_id": message_id,
                    "read_at": str(message.read_at),
                },
            )

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps(event))

    @staticmethod
    async def save_message(sender, receiver, message):
        print(sender, receiver, message)
        return await PrivateMessage.objects.acreate(
            sender=sender, receiver=receiver, encrypted_message=message
        )

    @staticmethod
    async def get_user(user_id):
        try:
            return await User.objects.aget(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    async def get_message(message_id):
        try:
            msg = await PrivateMessage.objects.aget(id=message_id)
            msg.encrypted_message = decrypt_message(msg.encrypted_message)
            return msg
        except PrivateMessage.DoesNotExist:
            return None
