from django.db import models
from djmoney.models.fields import MoneyField


class Category(models.Model):
    name = models.CharField(max_length=100, default="No category")

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, default='New product')
    description = models.CharField(max_length=300, null=True)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    image = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def __repr__(self):
        return 'Product name: ' + self.name + \
               ', Description: ' + self.description + \
               ', Price: ' + str(self.price) + \
               ', Category: ' + str(self.category) + \
               ', Image: ' + str(self.image)

