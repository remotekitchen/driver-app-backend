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
from apps.accounts.api.v1.serializers import UserSerializer, ProfileSerializer, VehicleSerializer
from apps.accounts.models import User, Profile, Vehicle
from django.shortcuts import get_object_or_404

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
      
class BaseProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]  
    serializer_class = ProfileSerializer

    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")

        if pk:
            profile = self.get_object(pk, request.user)
            if not profile:
                return self.handle_response({}, status_code=status.HTTP_404_NOT_FOUND, error="Profile not found")
            serializer = self.serializer_class(profile)
            return self.handle_response(serializer.data)
        else:
            profiles = Profile.objects.filter(user=request.user)
            serializer = self.serializer_class(profiles, many=True)
            return self.handle_response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")
        
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return self.handle_response(serializer.data, status_code=status.HTTP_201_CREATED)
            return self.handle_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.handle_response({}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))

    def put(self, request, pk):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")
        
        profile = self.get_object(pk, request.user)
        if not profile:
            return self.handle_response({}, status_code=status.HTTP_404_NOT_FOUND, error="Profile not found")
        
        try:
            serializer = self.serializer_class(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return self.handle_response(serializer.data)
            return self.handle_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.handle_response({}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")
        
        profile = self.get_object(pk, request.user)
        if not profile:
            return self.handle_response({}, status_code=status.HTTP_404_NOT_FOUND, error="Profile not found")
        profile.delete()
        return self.handle_response({"message": "Profile deleted successfully"}, status_code=status.HTTP_204_NO_CONTENT)

    def get_object(self, pk, user):
        try:
            return Profile.objects.get(pk=pk, user=user)
        except Profile.DoesNotExist:
            return None

    def handle_response(self, data, status_code=status.HTTP_200_OK, error=None):
        if error:
            return Response({'error': error}, status=status_code)
        return Response(data, status=status_code)
    




class BaseVehicleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VehicleSerializer

    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")

        if pk:
            vehicle = self.get_object(pk, request.user)
            if not vehicle:
                return self.handle_response({}, status_code=status.HTTP_404_NOT_FOUND, error="Vehicle not found")
            serializer = self.serializer_class(vehicle)
            return self.handle_response(serializer.data)
        else:
            vehicles = Vehicle.objects.filter(user=request.user)
            serializer = self.serializer_class(vehicles, many=True)
            return self.handle_response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")
        
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return self.handle_response(serializer.data, status_code=status.HTTP_201_CREATED)
            return self.handle_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.handle_response({}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))

    def put(self, request, pk):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")
        
        vehicle = self.get_object(pk, request.user)
        if not vehicle:
            return self.handle_response({}, status_code=status.HTTP_404_NOT_FOUND, error="Vehicle not found")
        
        try:
            serializer = self.serializer_class(vehicle, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return self.handle_response(serializer.data)
            return self.handle_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.handle_response({}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e))

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return self.handle_response({}, status_code=status.HTTP_401_UNAUTHORIZED, error="Authentication required")
        
        vehicle = self.get_object(pk, request.user)
        if not vehicle:
            return self.handle_response({}, status_code=status.HTTP_404_NOT_FOUND, error="Vehicle not found")
        vehicle.delete()
        return self.handle_response({"message": "Vehicle deleted successfully"}, status_code=status.HTTP_204_NO_CONTENT)

    def get_object(self, pk, user):
        try:
            return Vehicle.objects.get(pk=pk, user=user)
        except Vehicle.DoesNotExist:
            return None

    def handle_response(self, data, status_code=status.HTTP_200_OK, error=None):
        if error:
            return Response({'error': error}, status=status_code)
        return Response(data, status=status_code)