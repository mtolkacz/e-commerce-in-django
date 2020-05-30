from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField
from products.models import Product
from cart.models import PromoCode


class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=False, editable=False)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=False, editable=False)
    date = models.DateTimeField(default=timezone.now)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.PROTECT, null=True, editable=False)
