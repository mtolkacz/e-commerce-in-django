from cart.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()


def cart_context_processor(request):
    cart_dict = {}

    if request.user.id:
        try:
            cart_dict['cart'] = Order.objects.get(owner__id=request.user.id, is_ordered=False)
        except Order.DoesNotExist:
            pass
    elif request.session.session_key:
        try:
            cart_dict['cart'] = Order.objects.get(session_key=request.session.session_key, is_ordered=False)
        except Order.DoesNotExist:
            pass

    return cart_dict
