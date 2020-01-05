from django.db import models
from products.models import Product, Category
from accounts.models import UserProfile

MAX_ITEMS_IN_CART = 30


class OrderItem(models.Model):
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
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
    ref_code = models.CharField(max_length=20)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    is_ordered = models.BooleanField(default=False)
    # items = models.ForeignKey(OrderItem, on_delete=models.CASCADE, null=True)
    items = models.ManyToManyField(OrderItem)
    # payment_details = models.ForeignKey(Payment, null=True)
    date_ordered = models.DateTimeField(auto_now=True)

    def get_cart_items(self):
        return self.items.all().order_by('id')

    def get_cart_total(self):
        return sum([item.product.price*item.amount for item in self.items.all()])

    def __str__(self):
        return '{} - {}'.format(self.owner, self.ref_code)
