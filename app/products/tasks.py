from celery import shared_task
from gallop.celery import app
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def hello():
    print("Hej dziunia!")


@app.task(bind=True, ignore_result=False)
def send_email_shared(receiver, subject, message):
    # Send e-mail with activation link through SSL
    sender_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, sender_email, [receiver])
    return True


@shared_task()
def add(x, y):
    print("Test add {}".format(x+y))
    return x+y



