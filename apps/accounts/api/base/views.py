from allauth.socialaccount.providers.apple.client import AppleOAuth2Client
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialConnectView, SocialLoginView
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ParseError, PermissionDenied, ValidationError
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from apps.accounts.api.adapters import AppleOAuth2Adapter, GoogleOAuth2Adapter
from apps.accounts.api.base.serializers import (
    BaseChangePasswordSerializer,
    BaseEmailPasswordLoginSerializer,
    BaseUserSerializer,
    SocialLoginSerializer,
)
from apps.accounts.api.v1.serializers import UserSerializer, ProfileSerializer
from apps.accounts.models import User, Profile


class AbstractBaseLoginView(GenericAPIView):
    authentication_classes = []

    class Meta:
        abstract = True

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        user = serializer.validated_data.get("user")

        user_serializer = UserSerializer(instance=user, context={"request": request})
        token, _ = Token.objects.get_or_create(user=user)

        resp = {"token": token.key, "user_info": user_serializer.data}
        return Response(resp, status=status.HTTP_200_OK)


class BaseUserRegistrationAPIView(CreateAPIView):
    serializer_class = BaseUserSerializer


class BaseUserEmailVerifyView(APIView):
    def get(self, request, *args, **kwargs):
        uid = request.query_params.get("code", None)
        if not User.objects.filter(uid=uid).exists():
            return Response(
                {"message": "invalid request"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(uid=uid)
        if user.is_email_verified:
            return Response(
                {"message": "user already verified"}, status=status.HTTP_200_OK
            )

        user.is_email_verified = True
        user.save()
        return Response({"message": "user verified"}, status=status.HTTP_202_ACCEPTED)


class BaseEmailPasswordLoginAPIView(AbstractBaseLoginView):
    serializer_class = BaseEmailPasswordLoginSerializer


class BaseGoogleLoginAPIView(AbstractBaseLoginView):
    serializer_class = SocialLoginSerializer
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

    # def login(self):
    #     super().login()
    #     restaurant = self.request.data.get('restaurant', None)
    #     if restaurant is not None:
    #         RestaurantUser.objects.get_or_create(user=self.user, restaurant_id=restaurant)


class BaseGoogleConnectAPIView(SocialConnectView):
    adapter_class = GoogleOAuth2Adapter


class BaseAppleLoginAPIView(AbstractBaseLoginView):
    serializer_class = SocialLoginSerializer
    adapter_class = AppleOAuth2Adapter
    client_class = AppleOAuth2Client


class BaseUserRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BaseUserSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        location = request.query_params.get("location", None)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if location:
            restaurant = Location.objects.get(id=location).restaurant.id
            data["is_old_user"] = instance.is_old_user(restaurant=restaurant)
        return Response(data)


class BaseChangePasswordAPIView(UpdateAPIView):
    serializer_class = BaseChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        self.partial_update(request, *args, **kwargs)
        return Response(UserSerializer(instance=self.get_object()).data)






class BaseProfileListCreateView(generics.GenericAPIView):
    serializer_class = ProfileSerializer
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        """Retrieve the profile of the authenticated user."""
        try:
            profile = request.user.rider_profile  
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        """Create a new profile for the authenticated user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = Profile.objects.create_profile(request.user, serializer.validated_data)  # Use manager method
        return Response(self.get_serializer(profile).data, status=status.HTTP_201_CREATED)



class BaseProfileRetrieveUpdateDestroyView(generics.GenericAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve the user's profile."""
        try:
            profile = request.user.rider_profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        """Update the user's profile."""
        try:
            profile = request.user.rider_profile
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            updated_profile = Profile.objects.update_profile(profile, serializer.validated_data)  # Use manager method
            return Response(self.get_serializer(updated_profile).data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        """Delete the user's profile."""
        try:
            profile = request.user.rider_profile
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)