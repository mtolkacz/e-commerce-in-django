from collections import defaultdict
from random import random
from django.db import models
from django.db.models import Count
from django.apps import apps
from django.utils import timezone
import datetime as dt
import random
from calendar import monthrange
from products.models import Product, Brand
from cart.models import PromoCode
from sales.models import Sale


def get_popular_products(how_much=10, where=None):
    # where = {'area': 'department', 'object': department_object}
    lookup_field = 'product__' + where['area'] if where else None
    if lookup_field:
        product_list = list(Product.objects.filter(**{where['area']: where['object']})
                            .values_list('id', flat=True))
        sale_list = list(Sale.objects.filter(product__in=product_list)
                         .values_list('product', flat=True)
                         .annotate(total=Count('product'))
                         .order_by('-total')[:how_much])
    else:
        sale_list = list(Sale.objects.all()
                         .values_list('product', flat=True)
                         .annotate(total=Count('product'))
                         .order_by('-total')[:how_much])
    whens = []
    for sort_index, value in enumerate(sale_list):
        whens.append(models.When(id=value, then=sort_index))

    products = Product.objects.annotate(_sort_index=models.Case(*whens, output_field=models.IntegerField()))
    return products.order_by('_sort_index')[:how_much]


def get_popular_brands(amount=10):
    brand_list = list(Sale.objects.all()
                      .values_list('product__brand', flat=True)
                      .annotate(total=Count('product__brand'))
                      .order_by('-total')[:amount])
    whens = []
    for sort_index, value in enumerate(brand_list):
        whens.append(models.When(id=value, then=sort_index))

    brands = Brand.objects.annotate(_sort_index=models.Case(*whens, output_field=models.IntegerField()))
    return brands.order_by('_sort_index')[:amount]


# class from https://www.caktusgroup.com/blog/2019/01/09/django-bulk-inserts/
class BulkCreateManager(object):
    """
    This helper class keeps track of ORM objects to be created for multiple
    model classes, and automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.
    Upon completion of the loop that's `add()`ing objects, the developer must
    call `done()` to ensure the final set of objects is created for all models.
    """

    def __init__(self, chunk_size=100):
        self._create_queues = defaultdict(list)
        self.chunk_size = chunk_size

    def _commit(self, model_class):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(self._create_queues[model_key])
        self._create_queues[model_key] = []

    def add(self, obj):
        """
        Add an object to the queue to be created, and call bulk_create if we
        have enough objs.
        """
        model_class = type(obj)
        model_key = model_class._meta.label
        self._create_queues[model_key].append(obj)
        if len(self._create_queues[model_key]) >= self.chunk_size:
            self._commit(model_class)

    def done(self):
        """
        Always call this upon completion to make sure the final partial chunk
        is saved.
        """
        for model_name, objs in self._create_queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))


class SaleGenerator:
    def __init__(self, years=[2018, 2019, 2020], amount=1000, printonly=False):
        self.promo_list = [None, ] + list(PromoCode.objects.values_list('id', flat=True))
        self.promo_codes = PromoCode.objects.all()
        self.now = timezone.now()
        self.product_list = Product.objects.values_list('id', flat=True)
        self.products = Product.objects.all()
        self.sale_objects = []
        self.manager = BulkCreateManager()
        self.years = years
        self.amount = amount
        self.printonly = printonly

    def generate_date(self):
        year = random.choice(self.years)
        month = random.randint(1, 12) if year != self.now.year else random.randint(1, self.now.month) \
            if self.now.month > 1 else 1
        day = random.randint(1, self.now.day if year == self.now.year and month == self.now.month else
        monthrange(year, month)[1])
        return dt.datetime(year, month, day, tzinfo=timezone.utc)

    def generate_promo(self):
        promo_id = random.choice(self.promo_list)
        return self.promo_codes.get(id=promo_id) if promo_id else None

    def generate_product(self):
        return self.products.get(id=random.choice(self.product_list))

    def generate_sale(self):
        for i in range(self.amount):
            date = self.generate_date()
            product = self.products.get(id=random.choice(self.product_list))
            promo = self.generate_promo()
            if self.printonly:
                print(
                    f"Product: {product.name}, price: {product.price.amount}, date: {date}, promo: {promo.code if promo else None}")
            else:
                new_object = Sale(product=product, price=product.price, promo_code=promo, date=date)
                self.manager.add(new_object)
        self.manager.done()
