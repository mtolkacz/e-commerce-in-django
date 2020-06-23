from celery import shared_task
from gallop.celery import app
from .discount import *
from .models import *
import random


@app.task(bind=True, ignore_result=False)
def process_discount(self, instance_id):
    from .models import Discount
    from .discount import DiscountManager
    try:
        discount = Discount.objects.get(id=instance_id)
    except Discount.DoesNotExist:
        return False
    else:
        discount_manager = DiscountManager(discount)
        discount_manager.process()
        return True


@app.task(bind=True, ignore_result=False)
def finish_discount(self, instance_id):
    from .models import Discount
    try:
        discount = Discount.objects.get(id=instance_id)
    except Discount.DoesNotExist:
        return False
    else:
        discount_manager = DiscountManager(discount)
        discount_manager.finish()
        return True


def generate_dummy_product_stock():
    from products.models import Product
    products = Product.objects.all()
    for product in products:
        product.stock = random.randint(1, 150)
        product.save(update_fields=["stock"])





