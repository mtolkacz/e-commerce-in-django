from django.shortcuts import render, redirect
from .forms import ProductForm
from django.contrib import messages


def index(request):
    return render(request, 'index.html')


def test(request):
    return render(request, 'test.html')


def add(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name="dealer").exists():
            product_form = ProductForm()
            if request.method == 'POST':
                product_form = ProductForm(request.POST)
                if product_form.is_valid():
                    product_form.save()
                    messages.success(request, 'Product has been added.')
            return render(request, 'add_product.html',
                          {'product_form': product_form})

    return redirect('index')
