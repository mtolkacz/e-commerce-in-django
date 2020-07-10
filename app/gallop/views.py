import logging

from django.contrib.auth import get_user_model
from django.shortcuts import render_to_response

from blog.models import Post
from products.documents import ProductDocument
from products.models import Discount, LastViewedProducts

from .database import get_popular_brands, get_popular_products
from .error_views import *

logger = logging.getLogger(__name__)
User = get_user_model()


def handler404(request, exception, template_name="error/404.html"):
    response = render_to_response(template_name)
    response.status_code = 404
    return response


def search(request):
    if request.method == "POST":
        search_text = request.POST['search_text']
    else:
        search_text = ''
    products = ProductDocument.search().query('match', name=search_text)
    return render_to_response('products/ajax_search.html', {'products': products})


def index(request):
    popular_products = get_popular_products()
    popular_brands = get_popular_brands()
    posts = Post.objects.filter(status=1).order_by('-created_on')[:3]
    discounts = Discount.objects.filter(status=2).order_by('-priority')[:3]
    last_viewed_products = LastViewedProducts.objects.filter(user=request.user)[:5] if request.user.is_authenticated else None
    index_dict = {
        'products': popular_products,
        'brands': popular_brands,
        'posts': posts,
        'discounts': discounts,
        'last_viewed_products': last_viewed_products,
    }

    return render(request, 'products/index.html', index_dict)
