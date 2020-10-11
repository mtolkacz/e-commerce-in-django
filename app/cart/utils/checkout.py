from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from cart.forms import BillingForm, ShipmentForm, ShipmentTypeForm
from cart.models import Shipment, Order
from accounts.utils import create_user_from_form, update_user_from_form
from accounts.tasks import send_email


class Checkout:
    def __init__(self, request, cart):
        self.cart = cart
        self.request = request
        # create billing and shipment form
        self.billing_form = BillingForm()
        self.shipment_form = ShipmentForm(prefix='sh')
        self.shipmenttype_form = ShipmentTypeForm()
        self.context = {}  # template context dictionary
        self.user = self.cart.owner  # if no owner/NULL then None
        self.user_authenticated = request.user.is_authenticated  # check user authentication
        self.valid_forms = True  # if any form is not valid then set to false
        self.shipment = None  # create shipment when forms are validated

        self.same_address = request.POST.get("same-address", "")  # if billing address = shipment address
        self.account_checkbox = request.POST.get("account-checkbox", "")  # if user want to create account

        if self.same_address:
            self.context['same_address'] = 'checked'

        if self.account_checkbox:
            self.context['account_checkbox'] = 'checked'

    # create shipment from form, user or from request (looking for user)
    # need to pass form or user key and object
    def create_shipment(self, **kwargs):
        form = kwargs['form'] if 'form' in kwargs else None

        if form:
            try:
                voivodeship = Voivodeship.objects.get(name=form.cleaned_data['voivodeship'])
            except Voivodeship.DoesNotExist:
                voivodeship = None
            try:
                country = Country.objects.get(name=form.cleaned_data['country'])
            except Country.DoesNotExist:
                country = None
        else:
            voivodeship = self.user.voivodeship
            country = self.user.country

        return Shipment(order=self.cart,
                        type=self.shipmenttype_form.cleaned_data['delivery'],
                        first_name=form.cleaned_data['first_name'] if form else self.user.first_name,
                        last_name=form.cleaned_data['last_name'] if form else self.user.last_name,
                        city=form.cleaned_data['city'] if form else self.user.city,
                        voivodeship=voivodeship,
                        country=country,
                        zip_code=form.cleaned_data['zip_code'] if form else self.user.zip_code,
                        address_1=form.cleaned_data['address_1'] if form else self.user.address_1,
                        address_2=form.cleaned_data['address_2'] if form else self.user.address_2, )

    def set_context_data(self):
        self.context['checkout'] = True
        self.context['delivery_type_form'] = self.shipmenttype_form
        if self.user_authenticated:
            if self.user.has_all_billing_data():
                self.context['user_data'] = self.user
            else:
                billing_form = BillingForm(instance=self.user, without_new_account=True)
                self.context['billing_form'] = billing_form
                print(self.user.email)
        else:
            self.context['billing_form'] = self.billing_form

    def check_shipment_form(self):
        self.shipment_form = ShipmentForm(self.request.POST, prefix='sh')
        if not self.shipment_form.is_valid():
            self.valid_forms = False
        return self.valid_forms

    def check_billing_form(self):
        if self.account_checkbox:
            self.billing_form = BillingForm(self.request.POST)
        else:
            self.billing_form = BillingForm(self.request.POST, without_new_account=True)
        if not self.billing_form.is_valid() or not self.valid_forms:
            self.valid_forms = False
        return self.valid_forms

    def check_delivery_form(self):
        self.shipmenttype_form = ShipmentTypeForm(self.request.POST)
        if not self.shipmenttype_form.is_valid():
            self.valid_forms = False
        return self.valid_forms

    def get_shipment(self, **kwargs):
        if 'user' in kwargs:
            return self.create_shipment() if self.same_address else self.create_shipment(
                form=self.shipment_form)
        else:
            return self.create_shipment(form=self.billing_form) if self.same_address else self.create_shipment(
                form=self.shipment_form)

    def send_access_link(self):
        if self.cart.access_code:
            # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
            current_site = get_current_site(self.request)

            receiver = self.billing_form.cleaned_data['email']
            subject = 'Gallop purchase - {}'.format(self.cart.ref_code)
            context = {
                'first_name': self.billing_form.cleaned_data['first_name'],
                'domain': current_site.domain,
                'oidb64': urlsafe_base64_encode(force_bytes(self.cart.id)),
                'order': self.cart,
            }

            message = render_to_string('cart/access_link.html', context)

            # Celery sending mail
            send_email.apply_async((receiver, subject, message), countdown=0)
            send_email.apply_async(('michal.tolkacz@gmail.com', subject, message), countdown=0)
            messages.success(self.request, 'Link to purchase has been sent to your e-mail.')
        else:
            messages.error(self.request, 'No access key generated. Please contact administrator.')

    def update_cart(self, **kwargs):
        if self.cart:
            self.cart.is_ordered = True
            if 'user' in kwargs:
                self.cart.email = self.user.email
                self.cart.save(update_fields=['email', 'is_ordered'])
                self.cart.update_status(Order.CONFIRMED)

            else:
                # clean session info to protect order instance after session deleting when new user logged in
                self.cart.session_key = None

                # create user if user set checkbox
                if self.account_checkbox:
                    self.user = create_user_from_form(self.billing_form)

                    # pin existing cart to newly created user and clean session_key
                    self.cart.owner = self.user
                    self.cart.email = self.user.email
                    self.cart.save(update_fields=['email', 'owner', 'session_key', 'is_ordered'])

                # generate access key if user don't want an account
                else:
                    self.cart.create_access_code()
                    if self.billing_form.cleaned_data['email']:
                        self.cart.email = self.billing_form.cleaned_data['email']
                    elif self.shipment_form.cleaned_data['email']:
                        self.cart.email = self.shipment_form.cleaned_data['email']

                    self.cart.save(update_fields=['email', 'session_key', 'is_ordered'])

    def update_context_when_billing_form_failed(self):
        self.context['billing_form'] = self.billing_form

    def update_user(self):
        self.billing_form = BillingForm(self.request.POST, without_new_account=True)
        if self.billing_form.is_valid():
            update_user_from_form(self.billing_form, self.user)
        else:
            self.valid_forms = False