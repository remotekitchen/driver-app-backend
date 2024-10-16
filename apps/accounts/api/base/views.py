from accounts.api.adapters import AppleOAuth2Adapter, GoogleOAuth2Adapter
from accounts.api.base.serializers import (
    BaseChangePasswordSerializer,
    BaseContactSerializer,
    BaseEmailPasswordLoginSerializer,
    BaseRestaurantUserGETSerializer,
    BaseRestaurantUserSerializer,
    BaseUserAddressSerializer,
    BaseUserSerializer,
    SocialLoginSerializer,
)
from accounts.api.v1.serializers import UserSerializer
from accounts.models import Contacts, RestaurantUser, User, UserAddress
from allauth.socialaccount.providers.apple.client import AppleOAuth2Client
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from billing.models import Order
from core.api.mixins import GetObjectWithParamMixin
from core.utils import get_debug_str, get_logger
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

logger = get_logger()


class AbstractBaseLoginView(GenericAPIView):
    authentication_classes = []

    class Meta:
        abstract = True

    def post(self, request, *args, **kwargs):
        current_dt = timezone.now()
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(get_debug_str(request, request.user, serializer.errors))
            raise ValidationError(serializer.errors)

        user = serializer.validated_data.get("user")
        created = user.date_joined >= current_dt
        direct_order = request.query_params.get("direct_order", False)
        if not direct_order and user.role == User.RoleType.NA:
            raise PermissionDenied("User does not have any company!")

        user_serializer = UserSerializer(instance=user, context={"request": request})
        token, _ = Token.objects.get_or_create(user=user)

        resp = {
            "token": token.key,
            "user_info": user_serializer.data,
            "created": created,
        }

        # Get or Create a RestaurantUser instance for the logged in user
        restaurant = self.request.data.get("restaurant", None)
        location = self.request.data.get("location", None)
        if restaurant is not None:
            obj = RestaurantUser.objects.get_or_create(
                user=user, restaurant_id=restaurant
            )[0]
            resp["restaurantUser"] = BaseRestaurantUserSerializer(obj).data

            resp["is_old_user"] = user.is_old_user(restaurant=restaurant)

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


class BaseUserAddressListCreateAPIView(ListCreateAPIView):
    serializer_class = BaseUserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        is_default = self.request.query_params.get("is_default", None)
        if is_default:
            return UserAddress.objects.filter(user=self.request.user, is_default=True)
        return UserAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if serializer.validated_data.get("is_default"):
            UserAddress.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save(user=self.request.user)


class BaseUserAddressRetrieveUpdateDestroyAPIView(
    GetObjectWithParamMixin, RetrieveUpdateDestroyAPIView
):
    serializer_class = BaseUserAddressSerializer
    permission_classes = [IsAuthenticated, IsObjOwner]
    filterset_fields = ["id"]
    model_class = UserAddress

    def patch(self, request, *args, **kwargs):
        if "is_default" in request.data and request.data["is_default"] is True:
            UserAddress.objects.filter(user=request.user).update(is_default=False)
        return self.partial_update(request, *args, **kwargs)
