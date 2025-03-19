from rest_framework.views import APIView
from apps.chat.models import ChatMessage
from rest_framework.response import Response


class BaseGetChatHistoryView(APIView):
    def get(self, request, order_id):
        messages = ChatMessage.objects.filter(order_id=order_id).order_by("timestamp")

        if not messages.exists():
            return Response({"message": "No chat history found."}, status=204)

        return Response([
            {
                "sender": msg.sender_id,
                "message": msg.message,
                "timestamp": msg.timestamp,
            } for msg in messages
        ])
