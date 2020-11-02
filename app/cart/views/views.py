from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic.base import View

from accounts.models import account_activation_token
from cart.models import Order
from cart.utils import get_pending_cart
from cart.decorators import cart_required, order_required
from cart.viewmixins import PrepareCheckoutMixin, ShipmentMixin, CheckoutEmailMixin, \
     CheckoutContextMixin, SummaryContextMixing
from accounts.models.UserManager import create_from_form

User = get_user_model()


def cart(request):
    return render(request, 'cart/cart.html', {'order': get_pending_cart(request), })


@method_decorator(cart_required(), name='dispatch')
class CheckoutView(
    CheckoutContextMixin,
    PrepareCheckoutMixin,
    ShipmentMixin,
    CheckoutEmailMixin,
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
                self.user.update_from_form(self.billing_form)
            elif self.create_account:
                self.user = create_from_form(self.billing_form)

            self.cart.book()
            self.shipment = self.assign_new_shipment()

            if not self.shipment:
                messages.error(request,
                               'There was a problem creating the shipment. Administrator has been informed.')
            else:
                self.cart.update_after_shipment_creating(self.user, self.billing_form.cleaned_data['email'])
                self.send_checkout_email(request)

                # Save user and shipment after successful updating cart and sending checkout email
                if self.create_account:
                    self.user.save()

                self.shipment.save()

                if request.user.is_authenticated:
                    return redirect(reverse('summary', kwargs={'ref_code': self.cart.ref_code,
                                                               'oidb64': urlsafe_base64_encode(
                                                                   force_bytes(self.cart.id)), }))

            # Redirect newly created user or user without account to index page and display proper message
            return redirect(reverse('index'))


@method_decorator(order_required(), name='dispatch')
class SummaryView(SummaryContextMixing, View):
    template_name = 'cart/summary.html'
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        super().set_context_data(request, **kwargs)

        if self.permission == self.TEMP_ACCESS:
            self.access.delete()  # delete access model object to revoke an access to summary after revisit
            self.update_order_if_temp_access()

        if self.permission in self.HAS_ACCESS:
            return render(request, self.template_name, self.context)

        elif self.permission == self.NEED_ACCESS_CODE:
            self.order.create_access_code()
            self.send_link_with_access_code()

        return redirect(reverse('index'))


def purchase_activate(request, uidb64, token, oidb64):
    user = User.get_decrypted_object(uidb64)
    validated_token = account_activation_token.check_token(user, token)
    if not user and not validated_token:
        messages.error(request, 'Invalid activation link!')
        return redirect('login')
    else:
        user.activate()
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')  # Log in user
        order = Order.get_decrypted_object(oidb64)
        if not order:
            messages.error(request, 'Unable to find purchase. Contact with administrator.')
            return redirect('index')
        else:
            order.update_status(Order.CONFIRMED)
            return redirect(reverse('summary', kwargs={'ref_code': order.ref_code,
                                                       'oidb64': oidb64, }))
