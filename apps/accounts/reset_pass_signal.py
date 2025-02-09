from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens.
    When a token is created, an email needs to be sent to the user.
    """

    # Get absolute reset URL
    reset_url = instance.request.build_absolute_uri(
        reverse("password_reset:reset-password-confirm")
    ) + f"?token={reset_password_token.key}"

    context = {
        "current_user": reset_password_token.user.get_full_name() or reset_password_token.user.username,
        "username": reset_password_token.user.username,
        "email": reset_password_token.user.email,
        "reset_password_url": reset_url,
    }

    print(context)  # Debugging, remove this in production.
    # Render HTML email
    email_html_message = render_to_string("email/password_reset_email.html", context)

    # Send email
    msg = EmailMultiAlternatives(
        subject="Password Reset for Remote Kitchen",
        body=email_html_message,  # Plain text fallback
        from_email="info@remotekitchen.com",
        to=[reset_password_token.user.email],
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()
