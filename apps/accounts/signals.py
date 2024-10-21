from allauth.account.utils import perform_login
from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth import get_user_model
from django.dispatch import receiver

User = get_user_model()


@receiver(pre_social_login)
def link_to_local_user(sender, request, sociallogin, **kwargs):
    email_address = sociallogin.account.extra_data.get("email")
    if email_address:
        users = User.objects.filter(email=email_address)
        if users:
            perform_login(request, users[0], email_verification="optional")
