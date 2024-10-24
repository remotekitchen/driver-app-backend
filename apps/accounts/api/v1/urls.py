from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api.v1.views import (
    AppleLoginAPIView,
    ChangePasswordAPIView,
    EmailPasswordLoginAPIView,
    GoogleConnectAPIView,
    GoogleLoginAPIView,
    UserEmailVerifyView,
    UserRegistrationAPIView,
    UserRetrieveUpdateDestroyAPIView,
    ProfileListCreateView,
    ProfileRetrieveUpdateDestroyView

)

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("user/register/", UserRegistrationAPIView.as_view(), name="user-register"),
    path("user/verify/", UserEmailVerifyView.as_view(), name="user-verify"),
    path("login/email/", EmailPasswordLoginAPIView.as_view(), name="email-login"),
    path("login/google/", GoogleLoginAPIView.as_view(), name="google-login"),
    path("login/apple/", AppleLoginAPIView.as_view(), name="apple-login"),
    path("connect/google/", GoogleConnectAPIView.as_view(), name="google-connect"),
    path("user/item/", UserRetrieveUpdateDestroyAPIView.as_view(), name="user-item"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path(
        "password_reset/",
        include("django_rest_passwordreset.urls", namespace="password_reset"),
    ),
     path(
        "user/profile/",
        ProfileListCreateView.as_view(), name='profile-list-create',
    ),
       path(
        "user/profile/me",
        ProfileRetrieveUpdateDestroyView.as_view(), name='profile-detail-update-delete',
    ),
]
