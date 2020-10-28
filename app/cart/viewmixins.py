from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import Country, Voivodeship, send_email
from accounts.utils import send_activation_link
from cart.forms import ShipmentTypeForm, ShipmentForm, BillingForm
from cart.models import Shipment, Order
from cart.utils import send_purchase_link


class PrepareCheckoutMixin(object):

    @staticmethod
    def get_context_data(request, **kwargs):

        if request.user.is_authenticated:
            if request.user.has_all_billing_data():
                kwargs['has_all_billing_data'] = True
            else:
                kwargs['billing_form'] = BillingForm(instance=request.user, without_new_account=True)
        else:
            kwargs['billing_form'] = BillingForm()

        kwargs['shipment_form'] = ShipmentForm(prefix='sh')
        kwargs['shipmenttype_form'] = ShipmentTypeForm()

        return kwargs


class BaseCheckoutMixin(object):
    def __init__(self):
        self.cart = None
        self.same_address = None
        self.create_account = None
        self.user = None
        self.has_all_billing_data = None
        self.invalid_forms = False  # By default forms are valid. Set to invalid only on validation failure
        self.billing_form = None
        self.shipment = None
        self.shipment_form = None
        self.shipmenttype_form = None


class CheckoutFormsMixin(BaseCheckoutMixin):

    def validate_and_set_context(self, form_object, form_name, context):
        """ Assign form to global context and check validation
            valid_forms = False is breaking request processing """

        context[form_name] = form_object
        if not form_object.is_valid():
            self.invalid_forms = True

    def manage_billing_form(self, request, context):
        if not self.has_all_billing_data:
            if self.create_account:
                self.billing_form = BillingForm(request.POST)
            else:
                self.billing_form = BillingForm(request.POST, without_new_account=True)

            self.validate_and_set_context(self.billing_form, 'billing_form', context)

    def manage_shipment_form(self, request, context):
        """ If user wants to send shipment to different address than in billing address
            and same_address checkbox is not checked then get ShipmentForm from request and validate it
            billing address != shipment address """

        self.shipment_form = ShipmentForm(request.POST, prefix='sh')
        if not self.same_address:
            self.validate_and_set_context(self.shipment_form, 'shipment_form', context)
        else:
            # Load shipment form anyway, because user can click checkbox and load it again
            # However skip form validation if it's not necessary
            context['shipment_form'] = self.shipment_form

    def manage_shipmenttype_form(self, request, context):
        self.shipmenttype_form = ShipmentTypeForm(request.POST)
        self.validate_and_set_context(self.shipmenttype_form, 'shipmenttype_form', context)


class ShipmentMixin(BaseCheckoutMixin):

    def create_shipment(self, **kwargs):
        """ Create shipment from form, user or from request (looking for user)
            need to pass form or user key and object """

        if 'form' in kwargs or 'user' in kwargs:
            form = None
            if 'form' in kwargs:
                form = kwargs['form']
                try:
                    voivodeship = Voivodeship.objects.get(name=form.cleaned_data['voivodeship'])
                except Voivodeship.DoesNotExist:
                    voivodeship = None
                try:
                    country = Country.objects.get(name=form.cleaned_data['country'])
                except Country.DoesNotExist:
                    country = None
            elif 'user' in kwargs:
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

    def assign_new_shipment(self):
        """ Create new shipment based on few different options
            1. User's billing data
            2. Billing form
            3. Shipment form """

        if self.same_address:
            if self.user:
                return self.create_shipment(user=self.user)
            else:
                return self.create_shipment(form=self.billing_form)
        else:
            return self.create_shipment(form=self.shipment_form)


class CheckoutEmailMixin(BaseCheckoutMixin):

    def get_access_link_context(self, request):

        # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
        current_site = get_current_site(request)
        receiver = self.billing_form.cleaned_data['email']
        subject = 'Gallop purchase - {}'.format(self.cart.ref_code)
        mail_context = {
            'first_name': self.billing_form.cleaned_data['first_name'],
            'domain': current_site.domain,
            'oidb64': urlsafe_base64_encode(force_bytes(self.cart.id)),
            'order': self.cart,
        }

        return {
            'current_site': current_site,
            'receiver': receiver,
            'subject': subject,
            'mail_context': mail_context,
        }

    def send_access_email(self, request):
        if self.cart.access_code:
            context = self.get_access_link_context()

            mail_context = context['mail_context']
            receiver = context['receiver']
            subject = context['subject']

            message = render_to_string('cart/access_link.html', mail_context)

            # Celery's sending mail
            send_email.apply_async((receiver, subject, message), countdown=0)
            messages.success(request, 'Link to purchase has been sent to your e-mail.')
        else:
            messages.error(request, 'No access key generated. Please contact administrator.')

    def send_checkout_email(self, request):
        """ Send message with purchase link
            1. Authenticated user - a link to order's checkout
            2. Newly created user - account activation link and redirect to order's checkout
            3. User without account - a link and generated access code """

        if request.user.is_authenticated:
            send_purchase_link(request, self.cart, self.shipment)
        elif self.create_account:
            send_activation_link(request, self.cart.owner, order=self.cart)
        else:
            self.send_access_email()


class CartUpdateMixin(BaseCheckoutMixin):

    def update_cart_after_shipment_creating(self, request):

        self.cart.is_ordered = True
        fields_to_update = ['is_ordered', ]

        if request.user.is_authenticated:
            self.cart.email = self.user.email
            self.cart.status = Order.CONFIRMED
            fields_to_update.append('status')
        else:
            # Not authenticated user has deleted connection to Django session
            self.cart.session_key = None
            fields_to_update.append('session_key')

            if self.user:
                # Update owner and email fields in cart for newly created user
                self.cart.owner = self.user
                self.cart.email = self.user.email
                fields_to_update.append('owner')
            else:
                # User without account needs access code to display checkout
                self.cart.access_code = self.cart.get_access_code()
                self.cart.email = self.billing_form.cleaned_data['email']
                fields_to_update.append('access_code')

        # Email address is updated for every scenario
        fields_to_update.append('email')

        self.cart.save(update_fields=fields_to_update)


class CheckoutContextMixin(CheckoutFormsMixin):

    def get_context_data(self, request, **kwargs):

        # assign cart model object from cart_required - a decorator of dispatch method
        self.cart = kwargs['cart']

        if request.user.is_authenticated:
            self.user = request.user

            if self.user.has_all_billing_data():
                self.has_all_billing_data = True
                kwargs['has_all_billing_data'] = True
            else:
                self.has_all_billing_data = False
                self.manage_billing_form(request, kwargs)
        else:
            # If user want to create account / create_account checkbox is selected
            self.create_account = request.POST.get("create_account", "")
            kwargs['create_account'] = True if self.create_account else False
            self.manage_billing_form(request, kwargs)

        # If billing address = shipment address / same_address checkbox is selected
        self.same_address = request.POST.get("same_address", "")
        kwargs['same_address'] = True if self.same_address else False

        # Check shipment related forms
        self.manage_shipment_form(request, kwargs)
        self.manage_shipmenttype_form(request, kwargs)

        return kwargs
