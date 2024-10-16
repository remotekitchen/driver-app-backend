from allauth.account.utils import perform_login
from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Company, RestaurantUser, User
from billing.models import BillingProfile
from core.utils import get_logger
from marketing.models import FissionCampaign

logger = get_logger()


@receiver(post_save, sender=Company)
def create_billing_profile(sender, instance: Company, created, **kwargs):
    if not created:
        return
    try:
        BillingProfile.objects.create(company=instance)
    except Exception as e:
        logger.error(
            f'Billing profile create error for company {instance.id}::{e}')


@receiver(post_save, sender=RestaurantUser)
def check_new_login_rewards(sender, instance: RestaurantUser, created, **kwargs):
    try:
        # Handling fission campaigns
        allowed_availabilities = [
            FissionCampaign.Availability.ONCE_EVERY_USER,
            FissionCampaign.Availability.AFTER_SIGN_UP,
            FissionCampaign.Availability.AFTER_EVERY_ORDER
        ]
        q_exp = Q(availability__in=allowed_availabilities)
        q_exp &= Q(restaurant=instance.restaurant)
        campaign = FissionCampaign.objects.filter(q_exp).first()
        if campaign is not None:
            instance.available_lucky_draws.add(campaign)
    except Exception as e:
        logger.error(f'Login reward error: {e}')


User = get_user_model()


@receiver(pre_social_login)
def link_to_local_user(sender, request, sociallogin, **kwargs):
    email_address = sociallogin.account.extra_data.get('email')
    if email_address:
        users = User.objects.filter(email=email_address)
        if users:
            perform_login(request, users[0], email_verification='optional')
