from django.db import models
from apps.accounts.models import User
# Create your models here.

class TokenFCM(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(
        max_length=10,
        choices=[("web", "Web"), ("ios", "iOS")],
        default="web"  # Set a default value
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.device_type}"
