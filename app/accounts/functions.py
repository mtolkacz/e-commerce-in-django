from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tasks import send_email
from accounts.tokens import account_activation_token


def send_activation_link(request, user, **kwargs):

    # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
    current_site = get_current_site(request)

    # # Create Email object, prepare mail content and generate user token
    # # Email class includes custom predefined SMTP settings

    # receiver = form.cleaned_data.get('email')
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
