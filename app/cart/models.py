from django.db import models
from django.conf import settings
from products.models import Product, Category
from django.contrib.auth import get_user_model


User = get_user_model()
MAX_ITEMS_IN_CART = 30


class OrderItem(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)
    is_ordered = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now=True)
    date_ordered = models.DateTimeField(null=True)
    amount = models.IntegerField(default=1)

    def __str__(self):
        return self.product.name

    def get_item_total(self):
        return self.product.price * self.amount


class Order(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    ref_code = models.CharField(max_length=20)
    is_ordered = models.BooleanField(default=False)
    items = models.ManyToManyField(OrderItem)
    # payment_details = models.ForeignKey(Payment, null=True)
    date_ordered = models.DateTimeField(auto_now=True)

    def get_cart_items(self):
        return self.items.all().order_by('id')

    def get_cart_total(self):
        return sum([item.product.price*item.amount for item in self.items.all()])

    def __str__(self):
        return '{} - {}'.format(self.owner, self.ref_code)
