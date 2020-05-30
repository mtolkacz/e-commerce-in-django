from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login as auth_login
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from products.models import Product
from .models import *
from .extras import generate_order_id
from .models import Order, OrderAccess, Payment
from accounts.tokens import account_activation_token
from accounts.views import create_user_from_form, send_activation_link
from accounts.tasks import send_email
from .paypal import PaypalManager
from paypalcheckoutsdk.orders import paypalhttp
import json
from .checkout import Checkout
from .promocode import PromoCodeManager
from .summary import Summary
from sales.sale import SaleManager

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


# def delete_cart(request):
#     data = {}
#     existing_cart = get_pending_cart(request)
#     cart_deleted = existing_cart.delete()
#     if cart_deleted:
#         data['success'] = cart_deleted
#     return JsonResponse(data)


def delete_purchase(request):
    data = {}
    existing_cart = get_pending_cart(request)
    cart_deleted = existing_cart.delete()
    if cart_deleted:
        data['success'] = cart_deleted
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
def payment_cancelled(request):
    return render(request, 'cart/payment_cancelled.html', {})


@csrf_exempt
def payment_done(request):
    # return HttpResponse('Test')
    return render(request, 'cart/payment_done.html')


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
        ref_code is None) is False:
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


def process_payment(request):
    data = {}
    ref_code = request.GET.get('ref_code', 0)
    details_string = request.GET.get('details', 0)
    payment_details = json.loads(details_string)
    if payment_details and isinstance(payment_details, dict):
        payment_manager = PaypalManager(payment_details)
        try:
            payment_confirmed = payment_manager.confirm_payment()
        except paypalhttp.http_error.HttpError:
            payment_confirmed = None
        if payment_confirmed:
            try:
                order = Order.objects.get(ref_code=ref_code)
            except Order.DoesNotExist:
                order = None
            if order:
                payment = payment_manager.create_payment(order)
                if payment:
                    try:
                        shipment = Shipment.objects.get(order=order)
                    except Shipment.DoesNotExist:
                        shipment = None
                    if shipment:
                        shipment.update_status(Shipment.IN_PREPARATION)
                    sale = SaleManager(order)
                    sale.create_sale()
                order.update_status(Order.PAID)
                data['success'] = True
                data['order_id'] = order.id
    return JsonResponse(data)


@require_http_methods(['POST'])
def process_promo_code(request):
    data = {}
    code = request.POST.get('code', None)
    if not code:
        data['message'] = 'Promo code not provided'
    else:
        order = get_pending_cart(request)
        manager = PromoCodeManager(request, order, code)
        if not manager.promo_code:
            data['message'] = 'Incorrect promo code'
        else:
            already_used = manager.is_already_used()
            if already_used:
                data['message'] = 'Promo code already used'
            else:
                order = get_pending_cart(request)
                cart_total = order.get_cart_total()
                if not manager.meets_requirements(cart_total):
                    data['message'] = f"Minimum purchase total value for this promo code is " \
                                      f"{manager.promo_code.minimum_order_value}{str(cart_total.currency)}"
                else:
                    order.apply_promo_code(manager.promo_code)
                    manager.save_code_usage()
                    data = manager.get_context_data()
    return JsonResponse(data)


@require_http_methods(['POST'])
def delete_promo_code(request):
    data = {}
    order = get_pending_cart(request)
    code = request.POST.get('cart_id', None)
    if order and code:
        order.promo_code = None
        order.save(update_fields=['promo_code'])
        usage = PromoCodeUsage.objects.get(order=order)
        usage.delete()
        data['success'] = True
        messages.success(request, 'Promo code has been deleted')
    return JsonResponse(data)
