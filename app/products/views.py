from django.shortcuts import render, redirect
from .forms import ProductForm
from django.contrib import messages
from .models import Product, Category
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailView(DetailView):
    model = Product
    query_pk_and_slug = True
    template_name = 'products/product.html'
