from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from products.models import Product
from accounts.models import UserProfile
from .models import *
import datetime
from .extras import generate_order_id
from django.contrib import messages
from .forms import OrderForm
from django.http import JsonResponse, Http404, HttpResponseRedirect


# return user order object in cart if exists
def get_user_pending_cart(request):

    # get current logged-in user object otherwise return AnonymousUser
    # raise HTTP error code 404 if object exist
    user = get_object_or_404(UserProfile, user=request.user)

    order = Order.objects.filter(owner=user, is_ordered=False)
    if order.exists():
        return order[0]
    else:
        return 0


@login_required()
def add_to_cart(request, **kwargs):
    product = Product.objects.filter(id=kwargs.get('item_id', "")).first()
    user = get_object_or_404(UserProfile, user=request.user)
    if product:
        existing_cart = get_user_pending_cart(request)
        if existing_cart:
            order_item = existing_cart.items.filter(product=product).first()
            if order_item:
                order_item.amount = order_item.amount + 1
                order_item.save()
            else:
                order_item, status = OrderItem.objects.get_or_create(product=product, owner=user)
                if status:
                    existing_cart.items.add(order_item)
                    existing_cart.save()
        else:

            user_cart, status = Order.objects.get_or_create(owner=user, is_ordered=False)
            user_cart.ref_code = generate_order_id()
            if status:
                order_item = OrderItem.objects.create(product=product, owner=user)
                user_cart.items.add(order_item)
                user_cart.save()
        messages.info(request, "Product {} added to cart".format(product.name))
    return redirect(reverse('checkout'))


@login_required()
def delete_from_cart(request, item_id):
    item_to_delete = OrderItem.objects.filter(pk=item_id)
    if item_to_delete.exists():
        item_to_delete[0].delete()
        messages.info(request, "Item has been deleted")
    return redirect(reverse('cart:order_summary'))


@login_required()
def order_summary(request, **kwargs):
    existing_cart = get_user_pending_cart(request)
    context = {
        'cart': existing_cart
    }
    return render(request, 'order_summary.html', context)


@login_required()
def checkout(request):
    order = get_user_pending_cart(request)
    items = 0 if isinstance(order, int) else order.get_cart_items()
    cart_item_form = 0 if isinstance(items, int) else OrderForm(initial={'amount': items[0].amount})

    if request.method == 'POST':
        cart_item_form = OrderForm(request.POST)

    context = {
        'order': order,
        'items': items,
        'cart_item_form': cart_item_form,
    }
    return render(request, 'checkout.html', context)


@login_required()
def calculate_item_in_cart(request):
    item_id = request.GET.get('item_id', None)
    new_cart_value = request.GET.get('cart_value', None)

    # return if parameters not passed
    if item_id is None and new_cart_value is None:
        return redirect('checkout')

    # create empty dictionary for JsonResponse data
    data = {}

    try:
        # check if new cart value and item_id are integers
        value = int(new_cart_value)
        item_id = int(item_id)

        # get current logged-in user order and order items objects in cart
        updated_item = OrderItem.objects.get(pk=item_id)
        # updated_item = OrderItem.objects.filter(pk=item_id)

        # get current logged-in user order
        existing_cart = get_user_pending_cart(request)

    # render checkout site if request's arguments aren't integers
    # or if order or order item objects don't exist
    except (ValueError, Order.DoesNotExist, OrderItem.DoesNotExist) as e:
        return HttpResponseRedirect(reverse_lazy('checkout'))

    # check if value is in the right range
    if 0 < value <= MAX_ITEMS_IN_CART:
        try:
            success = OrderItem.objects.filter(pk=item_id).update(amount=value)
            data['success'] = success
            updated_item = OrderItem.objects.get(pk=item_id)

            # after successful update more data for JsonResponse
            if success:
                data['item_total_value'] = str(updated_item.get_item_total())
                data['cart_total_value'] = str(existing_cart.get_cart_total())

            # otherwise, raise an exception that cannot update record in database
            else:
                raise Http404('Cannot update OrderItem in database')
        except Http404 as error:
            return
    else:
        print('Incorrect product amount (max {} items)'.format(MAX_ITEMS_IN_CART))
        messages.error(request, 'Incorrect product amount (max {} items)'.format(MAX_ITEMS_IN_CART))
        data['success'] = False

    return JsonResponse(data)


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
    return render(request, 'success.html', {})



