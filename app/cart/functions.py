import string
import random
from datetime import date
import datetime

from django.contrib.sessions.models import Session
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import OrderItem, Order, Shipment
from .views import User
from accounts import tasks


def save_order_item(order):
    order_item = OrderItem.objects.get_or_create(order=order)
    order_item.save()
    return order_item


def generate_order_id():
    date_str = date.today().strftime('%Y%m%d')[2:] + str(datetime.datetime.now().second)
    rand_str = "".join([random.choice(string.digits) for count in range(3)])
    return date_str + rand_str


# return user/anonymous order object in cart if exists
def get_pending_cart(request):
    order = None
    if request.user.id:
        if request.user.is_authenticated:
            user = get_object_or_404(User, id=request.user.id)
            try:
                order = Order.objects.get(owner=user, is_ordered=False)
            except Order.DoesNotExist:
                pass
    elif request.session.session_key:
        try:
            session = Session.objects.get(session_key=request.session.session_key)
        except Session.DoesNotExist:
            pass
        else:
            try:
                order = Order.objects.get(session_key=session)
            except Order.DoesNotExist:
                pass
    return order


def send_purchase_link(request, order):
    # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
    current_site = get_current_site(request)

    first_name = order.owner.first_name if order.owner else None
    if not first_name:
        try:
            shipment = Shipment.objects.get(order=order)
        except Shipment.DoesNotExist:
            return False
        else:
            first_name = shipment.first_name

    receiver = order.email
    subject = 'Gallop purchase - {}'.format(order.ref_code)
    context = {
        'domain': current_site.domain,
        'oidb64': urlsafe_base64_encode(force_bytes(order.id)),
        'order': order,
        'first_name': first_name
    }

    message = render_to_string('cart/access_link.html', context)

    # Celery sending mail
    tasks.send_email.apply_async((receiver, subject, message), countdown=0)
    tasks.send_email.apply_async(('michal.tolkacz@gmail.com', subject, message), countdown=0)

    return True