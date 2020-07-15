from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField

from cart.models import PromoCode
from products.models import Product


class Sale(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        editable=False)

    price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='USD',
        editable=False)

    date = models.DateTimeField(
        default=timezone.now)

    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.PROTECT,
        null=True,
        editable=False)
