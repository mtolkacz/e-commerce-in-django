from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from products.models import Product
from accounts.models import UserProfile
from .models import OrderItem, Order
import datetime
from .extras import generate_order_id
from django.contrib import messages
from .forms import OrderForm


def get_user_pending_cart(request):
    user = get_object_or_404(UserProfile, user=request.user)
    order = Order.objects.filter(owner=user, is_ordered=False)
    if order.exists():
        return order[0]
    else:
        return 0


@login_required()
def add_to_cart(request, **kwargs):
    user = get_object_or_404(UserProfile, user=request.user)

    product = Product.objects.filter(id=kwargs.get('item_id', "")).first()

    order_item, status = OrderItem.objects.get_or_create(product=product)

    # increment product amount if already exist in cart
    if not status:
        order_item.amount = order_item.amount + 1
        order_item.save()

    # create order if product is new
    else:
        user_cart, status = Order.objects.get_or_create(owner=user, is_ordered=False)
        user_cart.items.add(order_item)
        if status:
            user_cart.ref_code = generate_order_id()
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
    # return render(request, 'checkout.html')
    order = get_user_pending_cart(request)
    items = order.items.all()
    cart_item_form = OrderForm(initial={'amount': items[0].amount})

    if request.method == 'POST':
        cart_item_form = OrderForm(request.POST)

    context = {
        'order': order,
        'items': items,
        'cart_item_form': cart_item_form,
    }
    return render(request, 'checkout.html', context)


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

    return redirect(reverse('cart:success'))


@login_required()
def success(request):
    return render(request, 'cart:success.html', {})
