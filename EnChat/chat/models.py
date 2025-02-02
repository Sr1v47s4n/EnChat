from django.db import models
from django.contrib.auth import get_user_model
from utils import encrypt_message, decrypt_message
User = get_user_model()


class PrivateMessage(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    encrypted_message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # Track if message is read
    read_at = models.DateTimeField(null=True, blank=True)  # Timestamp of read event

    def save(self, *args, **kwargs):
        self.encrypted_message = encrypt_message(self.encrypted_message)
        super().save(*args, **kwargs)

    def get_message(self):
        return decrypt_message(self.encrypted_message)
