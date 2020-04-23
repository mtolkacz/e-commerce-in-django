from cart.models import Order
from products.models import Product
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session

User = get_user_model()


def cart_processor(request):
    cart_dict = {}
    existing_cart = {}

    if request.user.username:
        user = User.objects.filter(username=request.user.username).first()

        if user:
            existing_cart = Order.objects.filter(owner=user, is_ordered=False).first()
    elif request.session.session_key:
        existing_cart = Order.objects.filter(session_key=request.session.session_key, is_ordered=False).first()

    if existing_cart:
        cart_dict = {'cart': existing_cart}

    return cart_dict
