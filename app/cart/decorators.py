from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode

from .models import Order
from .utils import get_pending_cart


def order_required():
    """ Display view only when order is found based on URL """

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            order = None
            try:
                ref_code = kwargs['ref_code']
                oidb64 = kwargs['oidb64']
                oid = force_text(urlsafe_base64_decode(oidb64))
            except(TypeError, ValueError, OverflowError):
                pass
            else:
                dict = {
                    'key': 'owner' if request.user.is_authenticated else 'owner__isnull',
                    'value': request.user if request.user.is_authenticated else True,
                }
                try:
                    order = Order.objects.get(**{dict['key']: dict['value']}, id=oid, ref_code=ref_code)
                except Order.DoesNotExist:
                    pass
            if order:
                kwargs['order'] = order
                return func(request, *args, **kwargs)
            else:
                return redirect(reverse('index'))
        return wrapper
    return decorator


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