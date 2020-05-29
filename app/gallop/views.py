from products.models import Product, ProductImage
from .error_views import *
from django.contrib.auth import get_user_model
from django.shortcuts import render_to_response
import logging
from products.documents import ProductDocument

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
    products = Product.objects.all()[:10]

    index_dict = {
        'products': products,
    }

    return render(request, 'products/index.html', index_dict)
