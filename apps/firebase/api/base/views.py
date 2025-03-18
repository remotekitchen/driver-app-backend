from  apps.firebase.models import TokenFCM
from rest_framework import status, viewsets
from apps.firebase.api.v1.serializers import FCMTokenSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.firebase.utils.fcm_helper import send_push_notification
from rest_framework.views import APIView


class BaseFCMTokenViewSet(viewsets.ModelViewSet):
    queryset = TokenFCM.objects.all()
    serializer_class = FCMTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        token = request.data.get("token")
        device_type = request.data.get("device_type", "web")

        # Check if this token already exists
        existing_token = TokenFCM.objects.filter(token=token).first()
        if existing_token:
            return Response({"message": "Token already exists", "token_id": existing_token.id})

        # 🔴 Remove this line to keep previous tokens
        # TokenFCM.objects.filter(user=user, device_type=device_type).delete()

        # Create a new token entry without deleting the old one
        fcm_token = TokenFCM.objects.create(user=user, token=token, device_type=device_type)

        return Response({"message": "Token registered successfully", "token_id": fcm_token.id})

    @action(detail=False, methods=["GET"])
    def get_user_tokens(self, request):
        """Retrieve all FCM tokens for the authenticated user"""
        user = request.user
        tokens = TokenFCM.objects.filter(user=user).values("id", "token", "device_type")

        return Response({"tokens": list(tokens)})




class BaseSendNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        title = request.data.get("title", "No Title")
        body = request.data.get("body", "No Body")
        send_to_all = request.data.get("send_to_all", False)  # Optional flag
        fcm_token = request.data.get("fcm_token")  # Specific token (optional)

        # Fetch all tokens for the current authenticated user
        tokens = list(TokenFCM.objects.filter(user=user).values_list("token", flat=True))

        # If `send_to_all` is False and `fcm_token` is provided, send to only that token
        if not send_to_all and fcm_token:
            tokens = [fcm_token] if fcm_token in tokens else []

        if not tokens:
            return Response({"error": "No valid FCM tokens found"}, status=400)

        try:
            data={
                  "campaign_title": title,
                  "campaign_message": body,
            }
            response = send_push_notification(tokens, data)
            return Response(response)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
