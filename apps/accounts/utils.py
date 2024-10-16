import uuid

from django.contrib.auth import get_user_model

from marketing.email_sender import send_email

User = get_user_model()


def get_verify_uid():
    while True:
        uid = uuid.uuid4()
        if User.objects.filter(uid=uid).exists():
            continue
        return uid


def send_verify_email(user):
    user.uid = get_verify_uid()
    user.save()
    verify_link = f'https://order.chatchefs.com/accounts/verify?code={user.uid}&hash={uuid.uuid4()}'
    subject = 'Verify your account'
    html_path = 'email/verify_email.html'
    print(verify_link)

    send_email(
        subject,
        html_path,
        context={
            'verify_link': verify_link,
            'user': user.get_full_name()
        },
        to_emails=[f'{user.email}']
    )
    return
