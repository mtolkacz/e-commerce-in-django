from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic.base import View

from accounts.utils import account_activation_token, send_activation_link, create_user_from_form, update_user_from_form
from cart.models import Order
from cart.utils import send_purchase_link, get_pending_cart, Summary
from cart.decorators import cart_required
from cart.viewmixins import BaseCheckoutMixin, PrepareCheckoutMixin, CheckoutFormsMixin, ShipmentMixin, CheckoutEmailMixin, \
    CartUpdateMixin, CheckoutContextMixin

User = get_user_model()


def cart(request):
    order = get_pending_cart(request)

    context = {
        'order': order,
    }
    return render(request, 'cart/cart.html', context)


@method_decorator(cart_required(), name='dispatch')
class CheckoutView(
    CheckoutContextMixin,
    PrepareCheckoutMixin,
    ShipmentMixin,
    CheckoutEmailMixin,
    CartUpdateMixin,
    View,
):
    template_name = 'cart/checkout.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, PrepareCheckoutMixin().get_context_data(request, **kwargs))

    def post(self, request, *args, **kwargs):

        kwargs = super().get_context_data(request, **kwargs)

        # Stop proceeding if any of form is incorrectly completed
        if self.invalid_forms:
            return render(request, self.template_name, kwargs)
        else:
            if not self.has_all_billing_data:
                update_user_from_form(self.billing_form, self.user)
            elif self.create_account:
                self.user = create_user_from_form(self.billing_form)

            self.cart.book()
            self.shipment = self.assign_new_shipment()

            if self.shipment:
                self.update_cart_after_shipment_creating(request)
                self.send_checkout_email(request)

                # Save user and shipment after successful updating cart and sending checkout email
                if self.create_account:
                    self.user.save()

                self.shipment.save()

                if request.user.is_authenticated:
                    return redirect(reverse('summary', kwargs={'ref_code': self.cart.ref_code,
                                                               'oidb64': urlsafe_base64_encode(
                                                                   force_bytes(self.cart.id)), }))
            else:
                messages.error(request,
                               'There was a problem creating the shipment. Administrator has been informed.')

            # Redirect newly created user or user without account to index page and display proper message
            return redirect(reverse('index'))


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
