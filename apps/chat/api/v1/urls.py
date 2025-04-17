from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.chat.api.v1.views import GetChatHistoryView

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("chat-history/<str:order_id>/", GetChatHistoryView.as_view(), name="chat-history"),
]
