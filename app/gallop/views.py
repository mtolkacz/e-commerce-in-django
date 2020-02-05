from products.models import Product
from django.shortcuts import render
from .error_views import *


def index(request):
    products = Product.objects.all()
    products_dict = {'products': products}
    return render(request, 'products/index.html', products_dict)
