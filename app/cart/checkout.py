from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from accounts.models import Voivodeship, Country
from .models import Shipment, Order
from .forms import BillingForm, ShipmentForm
from accounts.tasks import send_email
from accounts.views import create_user_from_form


class Checkout:
    def __init__(self, request, cart):
        self.cart = cart
        self.request = request
        # create billing and shipment form
        self.billing_form = BillingForm()
        self.shipment_form = ShipmentForm(prefix='sh')
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
        shipment = None
        if 'form' in kwargs:
            source = kwargs['form']
            if source:
                try:
                    voivodeship = Voivodeship.objects.get(name=source.cleaned_data['voivodeship'])
                    country = Country.objects.get(name=source.cleaned_data['country'])
                except (Voivodeship.DoesNotExist, Country.DoesNotExist):
                    pass
                else:
                    shipment = Shipment(order=self.cart,
                                        first_name=source.cleaned_data['first_name'],
                                        last_name=source.cleaned_data['last_name'],
                                        city=source.cleaned_data['city'],
                                        voivodeship=voivodeship,
                                        country=country,
                                        zip_code=source.cleaned_data['zip_code'],
                                        address_1=source.cleaned_data['address_1'],
                                        address_2=source.cleaned_data['address_2'], )
        else:
            source = self.user
            if source:
                shipment = Shipment(order=self.cart,
                                    first_name=source.first_name,
                                    last_name=source.last_name,
                                    city=source.city,
                                    voivodeship=source.voivodeship,
                                    country=source.country,
                                    zip_code=source.zip_code,
                                    address_1=source.address_1,
                                    address_2=source.address_2, )
        shipment.save() if shipment else None
        result = shipment
        return result

    def set_context_data(self):
        self.context['checkout'] = True
        if self.user_authenticated:
            if self.user.has_all_billing_data():
                self.context['user_data'] = self.user
            else:
                billing_form = BillingForm(instance=self.user, without_new_account=True)
                self.context['billing_form'] = billing_form
                # self.billing_form = billing_form
            # print('DJANGOTEST: {}', format(self.user.has_all_billing_data()))
        else:
            self.context['billing_form'] = self.billing_form

    def check_shipment_form(self):
        self.shipment_form = ShipmentForm(self.request.POST, prefix='sh')
        if not self.shipment_form.is_valid():
            self.valid_forms = False

    def is_valid_billing_form(self):
        if self.account_checkbox:
            self.billing_form = BillingForm(self.request.POST)
        else:
            self.billing_form = BillingForm(self.request.POST, without_new_account=True)
        return True if self.billing_form.is_valid() and self.valid_forms else False

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

    def update_user_from_billing_form(self):
        if 'billing_form' in self.context:
            self.billing_form = BillingForm(self.request.POST, without_new_account=True)
            if self.billing_form.is_valid():
                fields_to_update = []

                # todo probably not to elegant approach, but potentially save time on db operations
                if self.user.first_name != self.billing_form.cleaned_data['first_name']:
                    self.user.first_name = self.billing_form.cleaned_data['first_name']
                    fields_to_update.append('first_name')
                if self.user.last_name != self.billing_form.cleaned_data['last_name']:
                    self.user.last_name = self.billing_form.cleaned_data['last_name']
                    fields_to_update.append('last_name')
                if self.user.address_1 != self.billing_form.cleaned_data['address_1']:
                    self.user.address_1 = self.billing_form.cleaned_data['address_1']
                    fields_to_update.append('address_1')
                if self.user.address_2 != self.billing_form.cleaned_data['address_2']:
                    self.user.address_2 = self.billing_form.cleaned_data['address_2']
                    fields_to_update.append('address_2')
                if self.user.country != self.billing_form.cleaned_data['country']:
                    self.user.country = self.billing_form.cleaned_data['country']
                    fields_to_update.append('country')
                if self.user.voivodeship != self.billing_form.cleaned_data['voivodeship']:
                    self.user.voivodeship = self.billing_form.cleaned_data['voivodeship']
                    fields_to_update.append('voivodeship')
                if self.user.city != self.billing_form.cleaned_data['city']:
                    self.user.city = self.billing_form.cleaned_data['city']
                    fields_to_update.append('city')
                if self.user.zip_code != self.billing_form.cleaned_data['zip_code']:
                    self.user.zip_code = self.billing_form.cleaned_data['zip_code']
                    fields_to_update.append('zip_code')

                self.user.save(update_fields=fields_to_update)

            else:
                self.valid_forms = False
                print('DJANGOTEST: nie valid')
