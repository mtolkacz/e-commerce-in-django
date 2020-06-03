from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login as auth_login
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages

from .forms import BillingForm
from .models import *
from .models import Order
from accounts.tokens import account_activation_token
from accounts.views import send_activation_link
from accounts.tasks import send_email
from .checkout import Checkout
from .summary import Summary

User = get_user_model()


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


def cart(request):
    order = get_pending_cart(request)

    context = {
        'order': order,
    }
    return render(request, 'cart/cart.html', context)


def checkout(request):
    cart = get_pending_cart(request)
    if not cart:
        return redirect(reverse('index'))
    checkout = Checkout(request, cart)
    checkout.set_context_data()

    if request.method == 'POST':
        if not checkout.same_address:
            checkout.check_shipment_form()

        if not checkout.user:
            if checkout.is_valid_billing_form():
                checkout.shipment = checkout.get_shipment()
                if checkout.shipment:
                    checkout.cart.book()
                    checkout.update_cart()
                    if checkout.account_checkbox:
                        # method from accounts app to confirm new user and redirect to purchase
                        send_activation_link(checkout.request, checkout.user, order=checkout.cart)
                    else:
                        # send link to purchase with access key
                        checkout.send_access_link()
                else:
                    messages.error(request,
                                   'There was a problem creating the shipment. Administrator has been informed.')
            else:
                checkout.update_context_when_billing_form_failed()
            return redirect(reverse('index'))
        # if user logged in
        else:
            # if user had to fill billing form then update new personal data
            if 'billing_form' in checkout.context:
                checkout.update_user()
            if checkout.valid_forms:
                checkout.cart.book()
                checkout.shipment = checkout.get_shipment(user=checkout.user)
                # if saved shipment then go to finalize
                if checkout.shipment:
                    checkout.update_cart(user=checkout.user)
                    send_purchase_link(request, cart)
                    # go to checkout
                    return redirect(reverse('summary', kwargs={'ref_code': checkout.cart.ref_code,
                                                               'oidb64': urlsafe_base64_encode(
                                                                   force_bytes(checkout.cart.id)), }))
                else:
                    # todo track errors and inform administrator
                    messages.error(request,
                                   'There was a problem creating the shipment. Administrator has been informed.')
                return redirect(reverse('index'))
            checkout.context['billing_form'] = checkout.billing_form

    checkout.context['shipment_form'] = checkout.shipment_form

    return render(request, 'cart/checkout.html', checkout.context)


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
    send_email.apply_async((receiver, subject, message), countdown=0)
    send_email.apply_async(('michal.tolkacz@gmail.com', subject, message), countdown=0)

    return True


def summary(request, ref_code, oidb64):
    summary = Summary(request, ref_code, oidb64)

    if summary.set_order():
        if summary.set_shipment():
            summary.set_permission()
            if (summary.permission == summary.NO_ACCESS or
                    summary.permission == summary.TEMP_ACCESS or
                    summary.permission == summary.USER_AUTHENTICATED):
                summary.set_context()
                if summary.permission == summary.TEMP_ACCESS:
                    summary.has_access.delete()
                    summary.order.delete_access_code()
                    if summary.order.status < summary.order.CONFIRMED:
                        summary.order.update_status(Order.CONFIRMED)
                return render(request, 'cart/summary.html', summary.context)
            elif summary.permission == summary.NEED_ACCESS_CODE:
                summary.order.create_access_code()
                summary.send_link_with_access_code()
    return redirect(reverse('index'))


def purchase_activate(request, uidb64, token, oidb64):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        # Activate user and save
        user.is_active = True
        user.save()

        # Log in user
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        try:
            oid = int(force_text(urlsafe_base64_decode(oidb64)))
        except(TypeError, ValueError, OverflowError):
            oid = None
        if oid:
            try:
                from .models import Order
                order = Order.objects.get(id=oid)
            except Order.DoesNotExist:
                messages.error(request, 'Unable to find purchase. Contact with administrator.')
                return redirect('index')
            else:
                order.update_status(Order.CONFIRMED)
                return redirect(reverse('summary', kwargs={'ref_code': order.ref_code,
                                                           'oidb64': oidb64, }))
    else:
        messages.error(request, 'Invalid activation link!')
        return redirect('login')


