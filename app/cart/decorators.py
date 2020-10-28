from django.shortcuts import redirect
from django.urls import reverse
from .utils import get_pending_cart


def cart_required():
    """ Display view only when user has pending cart """

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            cart = get_pending_cart(request)
            if cart:
                kwargs['cart'] = cart
                return func(request, *args, **kwargs)
            else:
                return redirect(reverse('index'))
        return wrapper
    return decorator