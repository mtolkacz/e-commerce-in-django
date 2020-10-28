import re
import smtplib
import ssl

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import six

from .tasks import send_email
from cart.models import *


def send_activation_link(request, user, **kwargs):

    # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
    current_site = get_current_site(request)

    # # Create Email object, prepare mail content and generate user token
    # # Email class includes custom predefined SMTP settings

    receiver = user.email
    subject = 'Activate your Gallop account'
    if 'order' in kwargs:
        context = {
            'user': user,
            'domain': current_site.domain,
            # Return a bytestring version of user.pk and encode a bytestring to a base64 string
            # for use in URLs, stripping any trailing equal signs.
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            # Generate user token
            'token': account_activation_token.make_token(user),
            # Generate user token
            'oid': urlsafe_base64_encode(force_bytes(kwargs['order'].id)),
        }
        message = render_to_string('accounts/purchase_activate.html', context)
    else:
        context = {
            'user': user,
            'domain': current_site.domain,
            # Return a bytestring version of user.pk and encode a bytestring to a base64 string
            # for use in URLs, stripping any trailing equal signs.
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            # Generate user token
            'token': account_activation_token.make_token(user)
        }
        message = render_to_string('accounts/activate.html', context)
    # Celery sending mail
    send_email.apply_async((receiver, subject, message), countdown=0)
    messages.success(request, 'Please confirm your email address to complete the registration.')


def validate_zip_code(zip_code):
    result = re.match('^\d\d-\d\d\d$', zip_code)
    if result:
        return result
    else:
        raise ValidationError("Incorrect zip code. Please input value with XX-XXX format.")


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active)
        )


account_activation_token = TokenGenerator()


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


def update_user_from_form(form, user):
    if form.has_changed():
        fields_to_update = form.changed_data
        for field in form.changed_data:
            setattr(user, field, form.cleaned_data[field])

        user.save(update_fields=fields_to_update)


def create_user_from_form(form):
    # Save form but not commit yet
    user = form.save(commit=False)

    # Set deactivated till mail confirmation
    user.is_active = False

    # Create new user
    return user