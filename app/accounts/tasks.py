from gallop.celery import app
from django.core.mail import send_mail
from django.conf import settings


@app.task(bind=True, ignore_result=False)
def send_email(self, receiver, subject, message):
    # Send e-mail with activation link through SSL
    sender_email = settings.EMAIL_HOST_USER
    print(f"DJANGOTEST: EMAIL_HOST {settings.EMAIL_HOST}")
    print(f"DJANGOTEST: EMAIL_HOST_USER {settings.EMAIL_HOST_USER}")
    print(f"DJANGOTEST: EMAIL_HOST_PASSWORD {settings.EMAIL_HOST_PASSWORD}")
    print(f"DJANGOTEST: EMAIL_PORT {settings.EMAIL_PORT}")
    send_mail(subject, message, sender_email, [receiver])
    return True
