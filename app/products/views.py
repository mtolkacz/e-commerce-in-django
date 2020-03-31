from django.shortcuts import render, redirect
from .forms import ProductForm
from django.contrib import messages
from .models import Product, Category
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


def add(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name="dealer").exists():
            product_form = ProductForm()
            if request.method == 'POST':
                product_form = ProductForm(request.POST, request.FILES)
                if product_form.is_valid():
                    product_form.save(commit=False)
                    category_name = Category.objects.get(name=product_form.cleaned_data['category_name'])
                    product_form.category_name = category_name.id
                    product_form.save()
                    product_form = ProductForm()
                    messages.success(request, 'Product has been added.')
            return render(request, 'add_product.html',
                          {'product_form': product_form})

    return redirect('index')


class Show(ListView):
    model = Product
    queryset = Product.objects.all()
    template_name = 'show.html'


@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailView(DetailView):
    model = Product
    query_pk_and_slug = True
    template_name = 'products/product.html'
