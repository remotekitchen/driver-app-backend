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
    ProfileAPIView,
    VehicleAPIView,
    DriverSessionView,
    DriverStatusView

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
        ProfileAPIView.as_view(), name='profile-list-create',
    ),
       path(
        "user/profile/<int:pk>/",
        ProfileAPIView.as_view(), name='profile-detail',
    ),
      path(
        "user/vehicle/",
        VehicleAPIView.as_view(), name='vehicle-list-create',
    ),
       path(
        "user/vehicle/<int:pk>/",
        VehicleAPIView.as_view(), name='vehicle-detail-put-delete',
    ),
       path(
        "user/driver-session/",
        DriverSessionView.as_view(), name='driver-session-list-create',
    ),
       path('user/active-status/<int:pk>/', DriverSessionView.as_view(), name='active-status')
]
