from products.models import Product
from cart.models import Order
from django.shortcuts import render, get_object_or_404
from .error_views import *
from django.contrib.auth import get_user_model

User = get_user_model()


def index(request):
    products = Product.objects.all()[:10]
    index_dict = {'products': products}

    return render(request, 'products/index.html', index_dict)
