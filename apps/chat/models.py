from django.db import models
from django.utils import timezone

class ChatMessage(models.Model):
    order_id = models.CharField(max_length=255, blank=True, null=True)
    sender_id = models.IntegerField(blank=True, null=True)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now, blank=True, null=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.sender_id}: {self.message}"
