import random
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from products.models import Product
from .models import *
import datetime
from .extras import generate_order_id
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .forms import BillingForm, ShipmentForm
from django.contrib.auth import get_user_model
from .models import Order, OrderAccess
from accounts.tokens import account_activation_token
from django.contrib.auth import login as auth_login
from accounts.views import create_user_from_form, send_activation_link
from accounts.tasks import send_email
from accounts.models import Voivodeship, Country

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


def add_item_to_cart(request):
    item_id = request.GET.get('item_id', None)

    # create dictionary for JsonResponse data
    data = {'success': False}

    product = Product.objects.filter(id=item_id).first()

    if item_id and product:
        existing_cart = get_pending_cart(request)
        data['new_item'] = True
        if existing_cart:
            order_item = existing_cart.items.filter(product=product).first()
            if order_item:
                order_item.amount = order_item.amount + 1
                order_item.save()
                data['new_item'] = False
                data['success'] = True
                data['cart_qty'] = existing_cart.get_cart_qty()
                data['amount'] = str(order_item.amount)
            else:
                order_item = OrderItem.objects.create(product=product)

                if order_item:
                    existing_cart.items.add(order_item)
                    existing_cart.save()
                    data['success'] = True
                    data['cart_qty'] = existing_cart.get_cart_qty()
        else:
            if request.user.id:
                user = get_object_or_404(User, id=request.user.id)
                cart, status = Order.objects.get_or_create(owner=user, is_ordered=False)
            else:
                if not request.session.session_key:
                    request.session['guest'] = True
                    request.session.save()
                session = get_object_or_404(Session, session_key=request.session.session_key)
                cart, status = Order.objects.get_or_create(session_key=session, is_ordered=False)
            cart.ref_code = generate_order_id()
            if status:
                order_item = OrderItem.objects.create(product=product)
                cart.items.add(order_item)
                cart.save()
                existing_cart = cart
                data['success'] = True
                data['cart_qty'] = '1'
                data['new_cart'] = True
                data['cart_url'] = 'https://' + str(request.get_host()) + reverse('cart')

        data['cart_total_value'] = str(existing_cart.get_cart_total())
        data['item_id'] = item_id
        if data['new_item']:
            data['product_url'] = str(product.get_absolute_url())
            data['product_thumbnail_url'] = 'https://' + str(request.get_host()) + str(product.thumbnail.url)
            data['product_subdepartment_name'] = product.subdepartment.name
            data['product_name'] = product.name
            data['product_price'] = str(product.price if product.discounted_price is None else product.discounted_price)
        # messages.info(request, "Product {} added to cart".format(product.name))
    return JsonResponse(data)


def delete_cart(request):
    data = {}
    existing_cart = get_pending_cart(request)
    delete_cart_items = Order.objects.get(id=existing_cart.id).items.all().delete()
    if delete_cart_items:
        delete_cart = existing_cart.delete()
        if delete_cart:
            data['success'] = delete_cart

    return JsonResponse(data)


def delete_item_from_cart(request):
    item_id = request.GET.get('item_id', None)

    # create empty dictionary for JsonResponse data
    data = {}

    existing_cart = get_pending_cart(request)

    # return if parameters not passed
    if item_id is None or existing_cart is None:
        return JsonResponse(data)

    try:
        # check if new cart value and item_id are integers
        item_id = int(item_id)

    # render checkout site if request's argument isn't integer
    except ValueError:
        return JsonResponse(data)

    try:
        OrderItem.objects.get(order=existing_cart, product__id=item_id).delete()
    except OrderItem.DoesNotExist:
        data['success'] = False
    else:
        if existing_cart.items.first():
            data['success'] = True
            data['cart_total_value'] = str(existing_cart.get_cart_total())
            data['cart_qty'] = str(existing_cart.get_cart_qty())

        # remove cart if last product is deleted
        else:
            remove_cart = existing_cart.delete()
            data['remove_cart'] = remove_cart
    return JsonResponse(data)


def calculate_item_in_cart(request):
    item_id = request.GET.get('item_id', None)
    new_cart_value = request.GET.get('cart_value', None)

    # create empty dictionary for JsonResponse data
    data = {}

    # return if parameters not passed
    if item_id is None and new_cart_value is None:
        return JsonResponse(data)

    # get current logged-in user order
    existing_cart = get_pending_cart(request)

    try:
        # check if new cart value and item_id are integers
        value = int(new_cart_value)
        item_id = int(item_id)

        # get current logged-in user order and order items objects in cart
        updated_item = OrderItem.objects.get(order=existing_cart, product_id=item_id)

    # render checkout site if request's arguments aren't integers
    # or if order item objects don't exist
    except (ValueError, OrderItem.DoesNotExist):
        return JsonResponse(data)

    # check if value is in the right range
    if 0 < value <= MAX_ITEMS_IN_CART:
        updated_item.amount = value
        updated_item.save(update_fields=['amount'])  # todo how to make sure save was sucessfull?
        data['success'] = True

        # after successful update more data for JsonResponse
        data['amount'] = str(updated_item.amount)
        data['item_total_value'] = str(updated_item.get_item_total())
        if updated_item.is_discounted():
            data['old_price_checkout'] = str(updated_item.get_item_total_no_discount())
        data['cart_total_value'] = str(existing_cart.get_cart_total())
        data['cart_qty'] = str(existing_cart.get_cart_qty())
    else:
        messages.error(request, 'Incorrect product amount (max {} items)'.format(MAX_ITEMS_IN_CART))
        data['success'] = False

    return JsonResponse(data)


@login_required()
def order_summary(request, **kwargs):
    existing_cart = get_pending_cart(request)
    context = {
        'cart': existing_cart
    }
    return render(request, 'cart/order_summary.html', context)


def cart(request):
    order = get_pending_cart(request)

    context = {
        'order': order,
    }
    return render(request, 'cart/cart.html', context)


@csrf_exempt
def process_payment(request):
    return render(request, 'cart/process_payment.html', {})


@csrf_exempt
def payment_cancelled(request):
    return render(request, 'cart/payment_cancelled.html', {})


@csrf_exempt
def payment_done(request):
    # return HttpResponse('Test')
    return render(request, 'cart/payment_done.html')


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
                self.cart.confirm()

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
                checkout.cart.book()
                checkout.shipment = checkout.get_shipment()
                if checkout.shipment:
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
                checkout.update_user_from_billing_form()
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
                    messages.error('There was a problem creating the shipment. Administrator has been informed.')
                return redirect(reverse('index'))
            checkout.context['billing_form'] = checkout.billing_form

    checkout.context['shipment_form'] = checkout.shipment_form

    return render(request, 'cart/checkout.html', checkout.context)


# def checkout(request):
# existing_cart = get_pending_cart(request)
# if not existing_cart:
#     return redirect(reverse('index'))
#
# billing_form = BillingForm()
# shipment_form = ShipmentForm(prefix='sh') # need prefix cause contain fields with the same name as BillingForm
#
# context = {}
# user = existing_cart.owner  # if NULL then None
# user_authenticated = request.user.is_authenticated
# valid_forms = True
#
# if user_authenticated:
#     if user.has_all_billing_data() is False:
#         billing_form = BillingForm(instance=user)
#         context['billing_form'] = billing_form
#     else:
#         context['user'] = user
# else:
#     context['billing_form'] = billing_form
#
# if request.method == 'POST':
#
#     same_address = request.POST.get("same-address", "")  # billing address is also a shipment address
#     if not same_address:
#         shipment_form = ShipmentForm(request.POST, prefix='sh')
#         if not shipment_form.is_valid():
#             valid_forms = False

# if not user:
#     billing_form = BillingForm(request.POST)
#
#     # create account if account-checkbox is set
#     # account_checkbox = request.POST.get("account-checkbox", "")
#     if billing_form.is_valid() and valid_forms:
#
#         if same_address:
#             shipment = create_shipment(request, form=billing_form)
# #         else:
# #             shipment = create_shipment(request, form=shipment_form)
#
#         if shipment:
#             existing_cart.session_key = None
#             existing_cart.is_ordered = True
#
#             if account_checkbox:
#                 user = create_user_from_form(billing_form)
#
#                 # pin existing cart to newly created user and clean session_key
#                 existing_cart.owner = user
#                 existing_cart.save(update_fields=['owner', 'session_key', 'is_ordered'])
#
#                 send_activation_link(request, user, order=existing_cart)
#             else:
#                 access_code = random.randint(1000, 9999)
#                 existing_cart.access_code = access_code
#                 existing_cart.save(update_fields=['access_code', 'session_key', 'is_ordered'])
#                 self.send_link_with_access_code
#         else:
#             messages.error('There was a problem creating the shipment. Administrator has been informed.')
#
#         return redirect(reverse('index'))
#     else:
#         context['account_checkbox'] = 'checked'
#         context['billing_form'] = billing_form

# existing user section
# else:
#     if 'billing_form' in context:
#         billing_form = BillingForm(request.POST, instance=user)
#         if billing_form.is_valid():
#             billing_form.save()
#         else:
#             valid_forms = False

# if valid_forms:
#
#     # create shipment from existing user data if same_address checkbox or take data to shipment from ShipmentForm
#     if same_address:
#         shipment = create_shipment(request)
#     else:
#         shipment = create_shipment(request, form=shipment_form)

# if saved shipment then go to finalize
# if shipment:
#     oidb64 = urlsafe_base64_encode(force_bytes(existing_cart.id))
#     existing_cart.is_ordered = True
#     existing_cart.save(update_fields=['is_ordered'])
#     return redirect(reverse('summary', kwargs={'ref_code': existing_cart.ref_code,
#                                                'oidb64': oidb64, }))
# else:
#     # todo track errors and inform administrator
#     messages.error('There was a problem creating the shipment. Administrator has been informed.')
#
#         if same_address:
#             context['same_address'] = 'checked'
#         else:
#             shipment_form = ShipmentForm(request.POST)
#
# context['shipment_form'] = shipment_form
#
# return render(request, 'cart/checkout.html', context)


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


def get_access(request):
    data = {}
    try:
        access_code = request.GET.get('access_code', 0)
        access_code = int(access_code)
    except ValueError:
        access_code = None
    ref_code = request.GET.get('ref_code', '')
    purchase_key = request.GET.get('purchase_key', '')
    oid = int(force_text(urlsafe_base64_decode(purchase_key)))
    # if all parameters are correct then check order, instead return emtpy data dict
    if (access_code is None or
        purchase_key is None or
        access_code is None) is False:
        try:
            order = Order.objects.get(ref_code=ref_code, id=oid, access_code=access_code)
        except Order.DoesNotExist:
            pass
        else:
            if not request.session.session_key:
                request.session['guest'] = True
                request.session.save()
            try:
                session = Session.objects.get(session_key=request.session.session_key)
            except Session.DoesNotExist:
                session = None
            if session:
                new_order_access = OrderAccess(order=order, session_key=session)
                new_order_access.save()
                data['success'] = True
    return JsonResponse(data)


class Summary:
    # permission level
    NO_ACCESS = 1
    TEMP_ACCESS = 2
    USER_AUTHENTICATED = 3
    NEED_ACCESS_CODE = 4
    UNKNOWN_ERROR = None
    # permission level description
    # Order has access_code and no owner = no user and need access for session
    # 	1 - render access key page - no access
    # 	2 - render summary if - has access
    # Is Owner and and no access key = get context for user
    # 	3 - render summary
    # No access key and no owner = generate key and sent to e-mail
    # 	4 - go to main page and report that link has been sent
    # Unknown error
    # 	None - go to main page reporting unknown error

    def __init__(self, request, ref_code, oidb64):
        self.request = request
        self.ref_code = ref_code
        self.oidb64 = oidb64
        self.user_authenticated = request.user.is_authenticated
        self.user = self.get_user_object()
        self.session = self.get_or_create_user_session()
        self.context = {}
        self.order = None
        self.shipment = None
        self.unavailable_products = None
        self.has_access = None
        self.permission = None

    # 0.a) init
    def get_user_object(self):
        user = None
        if self.request:
            try:
                user = User.objects.get(id=self.request.user.id)
            except User.DoesNotExist:
                pass
        return user

    # 0.b) init
    def get_or_create_user_session(self):
        session = None
        if self.request:
            session = self.request.session.session_key
            if not session:
                self.request.session['guest'] = True
                self.request.session.save()
                session = self.request.session
            try:
                session = Session.objects.get(session_key=self.request.session.session_key)
            except Session.DoesNotExist:
                pass
        return session

    # 1.
    def set_order(self):
        self.order = self.get_encrypted_order()
        return self.order

    # 2.
    def set_shipment(self):
        self.shipment = self.get_shipment()
        if not self.shipment:
            messages.error("Couldn't find the shipment. Please contact with administrator.")
        return self.shipment

    # 3.
    def set_permission(self):
        self.permission = self.get_permission_level()

    # 4.
    def set_context(self):
        if self.permission:
            if self.permission == self.TEMP_ACCESS or self.permission == self.USER_AUTHENTICATED:
                self.context['user'] = self.user if self.user else self.shipment
                self.context['shipment'] = self.shipment
                self.context['api_key'] = str(settings.PAYPAL_API_KEY[0]) if settings.PAYPAL_API_KEY else ''
                self.context['order'] = self.order
            elif self.permission == self.NO_ACCESS:
                self.context['access_code'] = True
                self.context['ref_code'] = self.order.ref_code
                self.context['oidb64'] = self.oidb64

    def get_shipment(self):
        shipment = None
        if self.order:
            try:
                shipment = Shipment.objects.get(order=self.order)
            except Shipment.DoesNotExist:
                pass
        return shipment

    def get_encrypted_order(self):
        order = None
        try:
            oid = force_text(urlsafe_base64_decode(self.oidb64))
        except(TypeError, ValueError, OverflowError):
            pass
        else:
            dict = {
                'key': 'owner' if self.user_authenticated else 'owner__isnull',
                'value': self.user if self.user_authenticated else True,
            }
            try:
                order = Order.objects.get(**{dict['key']: dict['value']}, id=oid, ref_code=self.ref_code)
            except Order.DoesNotExist:
                pass
        return order

    def get_access_object(self):
        access = None
        if self.session:
            try:
                access = OrderAccess.objects.get(session_key=self.session)
            except OrderAccess.DoesNotExist:
                pass
        return access

    def send_link_with_access_code(self):
        if self.order:
            sent = send_purchase_link(self.request, self.order)
            if sent:
                messages.success(self.request, "Access code has been sent to your e-mail")
            else:
                messages.error(self.request, "Problem occured during sending access code. Contact with administrator")

    def get_permission_level(self):
        if self.order:
            if self.order.access_code and self.order.owner is None:
                self.has_access = self.get_access_object()
                if self.has_access:
                    return self.TEMP_ACCESS
                else:
                    return self.NO_ACCESS
            elif self.order.access_code is None and self.order.owner:
                return self.USER_AUTHENTICATED
            elif self.order.access_code is None and self.order.owner is None:
                return self.NEED_ACCESS_CODE
        return self.UNKNOWN_ERROR

    def set_unavailable_products(self):
        self.unavailable_products = self.get_unavailable_products()

    def get_unavailable_products(self):
        unavailable_products = None
        if self.order:
            items = self.order.items.filter(booked=False)
            products_ids = [items.values_list('product')]
            unavailable_products = Product.objects.filter(id__in=products_ids)
        return unavailable_products


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
                    if summary.order.confirmed is False:
                        summary.order.confirm()
                return render(request, 'cart/summary.html', summary.context)
            elif summary.permission == summary.NEED_ACCESS_CODE:
                summary.order.create_access_code()
                summary.send_link_with_access_code()
    return redirect(reverse('index'))


# def summary2(request, ref_code, oidb64):
#     from .models import Order
#     user_authenticated = request.user.is_authenticated
#     try:
#         oid = force_text(urlsafe_base64_decode(oidb64))
#     except(TypeError, ValueError, OverflowError):
#         pass
#     else:
#         try:
#             user = User.objects.get(id=request.user.id)
#         except User.DoesNotExist:
#             user = None
#         dict = {
#             'key': 'owner' if user_authenticated else 'owner__isnull',
#             'value': user if user_authenticated else True,
#         }
#         try:
#             order = Order.objects.get(**{dict['key']: dict['value']}, id=oid, ref_code=ref_code)
#         except Order.DoesNotExist:
#             messages.error(request, "Couldn't find the order. Please contact administrator.")
#             return redirect(reverse('index'))
#         else:
#             try:
#                 shipment = Shipment.objects.get(order=order)
#             except Shipment.DoesNotExist:
#                 messages.error("Couldn't find the shipment. Please contact with administrator.")
#                 return redirect(reverse('index'))
#             else:
#                 context = {}
#                 if order.access_code and order.owner is None:
#                     if not request.session.session_key:
#                         request.session['guest'] = True
#                         request.session.save()
#                     try:
#                         session = Session.objects.get(session_key=request.session.session_key)
#                     except Session.DoesNotExist:
#                         session = None
#
#                     if session:
#                         try:
#                             has_access = OrderAccess.objects.get(session_key=session)
#                         except OrderAccess.DoesNotExist:
#                             has_access = False
#                         if has_access:
#                             context['user'] = user if user else shipment
#                             context['shipment'] = shipment
#                             context['api_key'] = str(settings.PAYPAL_API_KEY[0])
#                             context['order'] = order
#                             has_access.delete()
#                             order.access_code = None
#                             order.save(update_fields=['access_code'])
#                         else:
#                             context['access_code'] = order.access_code
#                             context['ref_code'] = order.ref_code
#                             context['oidb64'] = oidb64
#                 elif order.access_code is None and order.owner:
#                     context['user'] = user if user else shipment
#                     context['shipment'] = shipment
#                     context['api_key'] = str(settings.PAYPAL_API_KEY[0])
#                     context['order'] = order
#                 elif order.access_code is None and order.owner is None:
#                     access_code = random.randint(1000, 9999)
#                     order.access_code = access_code
#                     order.save(update_fields=['access_code'])
#                     email_sent = send_link_with_access_code(request, order)
#                     if email_sent:
#                         messages.success(request, "Access code has been sent to your e-mail")
#                     else:
#                         messages.error(request, "Problem occured during sending access code. Contact with administrator")
#                     return redirect(reverse('index'))
#                 else:
#                     messages.error(request, "Unknown error. Please contact with administrator.")
#                     return redirect(reverse('index'))
#
#                 return render(request, 'cart/summary.html', context)


@login_required()
def update_transaction_records(request, cart_id):
    order_to_purchase = Order.objects.filter(pk=cart_id).first()
    order_to_purchase.is_completed = True
    order_to_purchase.date_completed = datetime.datetime.now()
    order_to_purchase.save()
    order_items = order_to_purchase.items.all()
    order_items.update(is_completed=True, date_completed=datetime.datetime.now())

    return redirect(reverse('success'))


@login_required()
def success(request):
    return render(request, 'cart/success.html', {})


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
        else:
            try:
                from .models import Order
                order = Order.objects.get(id=oid)
            except Order.DoesNotExist:
                messages.error(request, 'Unable to find purchase. Contact with administrator.')
                return redirect('index')
            else:
                order.confirm()
                return redirect(reverse('summary', kwargs={'ref_code': order.ref_code,
                                                           'oidb64': oidb64, }))
    else:
        messages.error(request, 'Invalid activation link!')
        return redirect('login')


def delete_purchase(request):
    data = {}
    cart = get_pending_cart(request)
    if not cart.is_ordered:
        cart.delete_order()
        data['success'] = True
        messages.success(request, 'Purchase has been deleted')
    return JsonResponse(data)
