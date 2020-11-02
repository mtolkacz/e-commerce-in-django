import re
import smtplib
import ssl

from django.conf import settings
from django.core.exceptions import ValidationError

from .tasks import send_email
from cart.models import *


def validate_zip_code(zip_code):
    result = re.match('^\d\d-\d\d\d$', zip_code)
    if result:
        return result
    else:
        raise ValidationError("Incorrect zip code. Please input value with XX-XXX format.")


class Email:
    def __init__(self):
        self.smtp_server = settings.EMAIL_HOST
        self.port = settings.EMAIL_PORT
        self.sender_email = settings.EMAIL_HOST_USER
        self.password = settings.EMAIL_HOST_PASSWORD

    def send(self, subject, message, receiver):
        message = 'Subject: {}\n\n{}'.format(subject, message)
        context = ssl.create_default_context()
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.starttls(context=context)
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, receiver, message)
