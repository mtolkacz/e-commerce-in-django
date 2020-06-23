from __future__ import absolute_import, unicode_literals
from gallop.celery import app
from django.core.mail import send_mail
from django.conf import settings

from celery import shared_task

from .email import Email
from products.models import Product


@app.task(bind=True, ignore_result=False)
def send_email(self, receiver, subject, message):
    # Send e-mail with activation link through SSL
    sender_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, sender_email, [receiver])
    return True


@shared_task
def add(x, y):
    return x+y


@app.task(bind=True, ignore_result=False)
def get_first_product(self):
    p = Product.objects.first()
    return p.id
