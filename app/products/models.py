from django.db import models
from djmoney.models.fields import MoneyField


class Product(models.Model):
    name = models.CharField(max_length=100, default='New product')
    description = models.CharField(max_length=300, null=True)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')

    def __repr__(self):
        return 'Product name: ' + self.name + ', Description: ' + self.description + ', Price: ' + str(self.price)
