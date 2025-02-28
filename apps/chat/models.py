from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from apps.billing.models import Delivery

User = get_user_model()

class ChatMessage(models.Model):
    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="chat_messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    message = models.TextField(verbose_name=_("Message"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))
    is_read = models.BooleanField(default=False, verbose_name=_("Is Read"))

    def __str__(self):
        return f"Chat ({self.delivery.id}) - {self.sender} to {self.receiver}"

    class Meta:
        ordering = ["timestamp"]
