from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.api.v1.views import (AppleLoginAPIView, ChangePasswordAPIView,
                                   ContactModelAPIView,
                                   EmailPasswordLoginAPIView,
                                   GoogleConnectAPIView, GoogleLoginAPIView,
                                   RestaurantUserAPIView,
                                   RestaurantUserRetrieveAPIView,
                                   UserAddressListCreateAPIView,
                                   UserAddressRetrieveUpdateDestroyAPIView,
                                   UserEmailVerifyView,
                                   UserRegistrationAPIView,
                                   UserRetrieveUpdateDestroyAPIView)

router = DefaultRouter()
router.register("contacts", ContactModelAPIView, basename="contacts")

urlpatterns = [
    path("", include(router.urls)),
    path('user/register/', UserRegistrationAPIView.as_view(), name='user-register'),
    path('user/verify/', UserEmailVerifyView.as_view(), name='user-verify'),
    path('login/email/', EmailPasswordLoginAPIView.as_view(), name='email-login'),
    path('login/google/', GoogleLoginAPIView.as_view(), name='google-login'),
    path('login/apple/', AppleLoginAPIView.as_view(), name='apple-login'),
    path('connect/google/', GoogleConnectAPIView.as_view(), name='google-connect'),
    path('user/item/', UserRetrieveUpdateDestroyAPIView.as_view(), name='user-item'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change-password'),
    path('restaurant-users/<str:pk>/', RestaurantUserAPIView.as_view(),
         name='restaurant-user'),
    path('restaurant-user/', RestaurantUserRetrieveAPIView.as_view(),
         name='restaurant-user'),
    path('user-address/', UserAddressListCreateAPIView.as_view(), name='user-address'),
    path('user-address/item/', UserAddressRetrieveUpdateDestroyAPIView.as_view(),
         name='user-address-itemI'),
    path('password_reset/', include('django_rest_passwordreset.urls',
         namespace='password_reset')),

]
