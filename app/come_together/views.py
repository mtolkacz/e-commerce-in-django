from products.models import Product
from django.shortcuts import render


def index(request):
    products = Product.objects.all()
    products_dict = {'products': products}
    return render(request, 'index.html', products_dict)