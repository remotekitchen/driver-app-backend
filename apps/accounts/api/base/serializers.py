from accounts.models import Company, Contacts, RestaurantUser, User, UserAddress
from accounts.utils import send_verify_email
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.base import AuthProcess
from billing.models import Order
from dj_rest_auth.registration.serializers import (
    SocialLoginSerializer as BaseSocialLoginSerializer,
)
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError


class SocialLoginSerializer(BaseSocialLoginSerializer):
    def get_social_login(self, *args, **kwargs):
        """
        Set the social login process state to connect rather than login
        Refer to the implementation of get_social_login in base class and to the
        allauth.socialaccount.helpers module complete_social_login function.
        """
        social_login = super().get_social_login(*args, **kwargs)
        social_login.state["process"] = AuthProcess.CONNECT
        return social_login


class BaseUserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        max_length=255, write_only=True, required=False
    )
    code = serializers.CharField(max_length=25, write_only=True, required=False)

    refer_code = serializers.CharField(max_length=25, write_only=True, required=False)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    # token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "phone",
            "company_name",
            "reward_points",
            "code",
            "refer_code",
            "date_of_birth",
        ]
        extra_kwargs = {
            "reward_points": {
                "read_only": True,
            }
        }

    def get_name(self, obj: User):
        return f"{obj.first_name} {obj.last_name}"

    # def get_token(self, obj: User):
    #     return Token.objects.get(user=obj).key

    def to_representation(self, instance: User):
        representation = super(BaseUserSerializer, self).to_representation(instance)
        company = instance.company
        if company is not None:
            representation["company_name"] = company.name
        return representation

    def validate(self, attrs):
        if self.context["request"].method == "PATCH" and "password" in attrs:
            attrs.pop("password")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")

        invite_obj = None
        if "refer_code" in validated_data:
            invite_code = validated_data.pop("refer_code")

            if not InviteCodes.objects.filter(code=invite_code).exists():
                raise ValidationError({"invite_code": _("This invite code invalid!")})

            invite_obj = InviteCodes.objects.get(code=invite_code)

        if "company_name" in validated_data:
            company_name = validated_data.pop("company_name")
            company = Company.objects.create(name=company_name)
            role = User.RoleType.OWNER
            validated_data["company"] = company
            validated_data["role"] = role

        if "code" in validated_data:
            company_code = validated_data.pop("code")
            if not Company.objects.filter(register_code=company_code).exists():
                raise ValidationError(
                    {"register_code": _("This register code is invalid!")}
                )

            company = Company.objects.get(register_code=company_code)
            role = User.RoleType.EMPLOYEE
            validated_data["company"] = company
            validated_data["role"] = role

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save(update_fields=["password"])
        Token.objects.create(user=user)

        if invite_obj:
            invite_obj.status = InviteCodes.STATUS.ACCEPTED

            refer_obj = invite_obj.refer
            refer_obj.joined_users.add(user)
            if not refer_obj.invited_users.filter(id=user.id).exists():
                refer_obj.invited_users.add(user)
            invite_obj.save()

        send_verify_email(user)

        return user


class BaseEmailPasswordLoginSerializer(serializers.Serializer):
    email = serializers.CharField(label=_("Email"), write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(label=_("Token"), read_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), email=email, password=password
            )

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(msg, code="authorization")
            # if not user.is_email_verified:
            #     msg = _(
            #         'Error: Please verify your email address to proceed with the login.')
            #     raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class BaseChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    old_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ("old_password", "password")

    def validate_old_password(self, value):
        user = self.context["request"].user
        if SocialAccount.objects.filter(user=user).exists():
            return value
        if not user.check_password(value):
            raise serializers.ValidationError(
                {"old_password": "Old password is not correct"}
            )
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data["password"])
        instance.save()

        return instance


class BaseUserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = "__all__"
        extra_kwargs = {"user": {"read_only": True}}
