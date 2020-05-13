from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from products.models import Product
from .models import *
import datetime
from .extras import generate_order_id
from django.contrib import messages
from django.http import JsonResponse, Http404
from .forms import CheckoutForm
# User = settings.AUTH_USER_MODEL
from django.contrib.auth import get_user_model


User = get_user_model()


# return user/anonymous order object in cart if exists
def get_pending_cart(request):
    order = False
    if request.user.username:
        if request.user.is_authenticated:
            user = get_object_or_404(User, username=request.user.username)
            try:
                order = Order.objects.get(owner=user, is_ordered=False)
            except Order.DoesNotExist:
                pass
    elif request.session.session_key:
        try:
            session = Session.objects.get(session_key=request.session.session_key)
        except Session.DoesNotExist:
            return 0
        else:
            try:
                order = Order.objects.get(session_key=session)
            except Order.DoesNotExist:
                return 0
    return order if order else 0


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
            if request.user.username:
                user = get_object_or_404(User, username=request.user.username)
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
            messages.info(request, "Item has been deleted")
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


def checkout(request):
    form = CheckoutForm()
    return render(request, 'cart/checkout.html', {'form': form})


@login_required()
def process_payment(request, cart_id):
    return redirect(reverse('cart:update_records',
                            kwargs={
                                'cart_id': cart_id,
                            })
                    )


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



