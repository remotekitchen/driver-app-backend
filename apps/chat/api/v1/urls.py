from django.urls import path
from apps.chat.api.v1.views import GetChatHistoryView

urlpatterns = [
    path("chat/<str:order_id>/", GetChatHistoryView.as_view()),
]
