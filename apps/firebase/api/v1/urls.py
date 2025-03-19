from django.urls import path
from apps.firebase.api.v1.views import FCMTokenViewSet, SendNotificationView


urlpatterns = [
  path('fcm-tokens/', FCMTokenViewSet.as_view({'get': 'list', 'post': 'create'}), name='fcm-token-list'),
  path("send-notification/", SendNotificationView.as_view(), name="send-notification"),
]
