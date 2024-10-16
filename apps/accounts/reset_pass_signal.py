
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse

from django_rest_passwordreset.signals import reset_password_token_created
from food.models import Location, Restaurant


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    res_id=int(instance.request.data['res_id']) #21
    location_id=int(instance.request.data['location_id']) #11


    res_slug=Restaurant.objects.get(id=res_id).slug
    location_slug=Location.objects.get(id=location_id).slug

    print(res_slug, location_slug)
    # send an e-mail to the user
    context = {
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': "{}?token={}".format(f'https://order.chatchefs.com/{res_slug}/{location_slug}/account/password-reset',
            reset_password_token.key)
    }
    print(context)
    # render email text
    email_html_message = render_to_string('email/password_reset_email.html', context)
    email_plaintext_message = render_to_string('email/password_reset_email.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(title="ChatChefs.com"),
        # message:
        email_html_message,
        # from:
        'info@chatchefs.com',
        # to:
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()
    
