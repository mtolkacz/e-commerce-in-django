from products.models import Product, ProductImage
from .error_views import *
from django.contrib.auth import get_user_model
from django.shortcuts import render_to_response
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def handler404(request, exception, template_name="error/404.html"):
    response = render_to_response(template_name)
    response.status_code = 404
    return response


def index(request):
    products = Product.objects.all()[:10]
    logger.info("I'm on mainpage!")

    index_dict = {
        'products': products,
    }

    return render(request, 'products/index.html', index_dict)
