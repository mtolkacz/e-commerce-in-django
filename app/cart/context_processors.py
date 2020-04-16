from cart.models import Order
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()


def cart_processor(request):
    username = request.user.username

    cart_dict = {}

    if username:
        user = User.objects.filter(username=username).first()

        if user:
            existing_cart = Order.objects.filter(owner=user, is_ordered=False).first()

            if existing_cart:
                cart_dict = {'cart': existing_cart}
                products = Product.objects.filter

    return cart_dict
