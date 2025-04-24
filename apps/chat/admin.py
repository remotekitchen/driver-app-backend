from django.contrib import admin
from apps.chat.models import ChatMessage

# Register your models here.
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
  list_display = ["sender_name", "message", "timestamp"]
  search_fields = ["sender_name", "message"]
  list_filter = ["timestamp"]
  date_hierarchy = "timestamp"