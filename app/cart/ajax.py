import json

import paypalhttp
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_http_methods
from products.models import Product
from sales.sale import SaleManager

from .functions import generate_order_id, get_pending_cart
from .models import OrderItem, Order, MAX_ITEMS_IN_CART, OrderAccess, Shipment, PromoCodeUsage
from .paypal import PaypalManager
from .promocode import PromoCodeManager
from .views import User


@require_http_methods(['POST'])
def add_item_to_cart(request):
    item_id = request.POST.get('item_id', None)

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


def delete_purchase(request):
    data = {}
    existing_cart = get_pending_cart(request)
    cart_deleted = existing_cart.delete()
    if cart_deleted:
        data['success'] = cart_deleted
    return JsonResponse(data)


@require_http_methods(['POST'])
def delete_item_from_cart(request):
    item_id = request.POST.get('item_id', None)

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


@require_http_methods(['POST'])
def calculate_item_in_cart(request):
    item_id = request.POST.get('item_id', None)
    new_cart_value = request.POST.get('cart_value', None)

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


@require_http_methods(['POST'])
def get_access(request):
    data = {}
    try:
        access_code = request.POST.get('access_code', 0)
        access_code = int(access_code)
    except ValueError:
        access_code = None
    ref_code = request.POST.get('ref_code', '')
    purchase_key = request.POST.get('purchase_key', '')
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
                data['message'] = 'Access denied. Wrong access code.'
    return JsonResponse(data)


@require_http_methods(['POST'])
def process_payment(request):
    data = {}
    ref_code = request.POST.get('ref_code', 0)
    details_string = request.POST.get('details', 0)
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
                cart_total = order.get_cart_total()
                if not manager.meets_requirements(cart_total):
                    data['message'] = f"Minimum purchase total value for this promo code is " \
                                      f"{manager.promo_code.minimum_order_value}{str(cart_total.currency)}"
                else:
                    order.apply_promo_code(manager.promo_code)
                    manager.save_code_usage()
                    order = get_pending_cart(request)
                    data = manager.get_context_data(order)
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