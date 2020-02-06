from django.db import models
from djmoney.models.fields import MoneyField
from django.utils.html import mark_safe
from django.core.validators import MaxValueValidator, MinValueValidator
from accounts.models import User


class Department(models.Model):
    name = models.CharField(max_length=100, default="No department")

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name


class Subdepartment(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=100, default="No subdepartment")

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name


class Category(models.Model):
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=100, default="No category")

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, default='New product')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True)
    description = models.TextField(max_length=1500, null=True)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.PROTECT, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    thumbnail = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.thumbnail)

    image_tag.short_description = 'Image'

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Product name: ' + self.name + \
               ', Description: ' + self.description + \
               ', Price: ' + str(self.price) + \
               ', Category: ' + str(self.category) + \
               ', Image: ' + str(self.thumbnail)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image)

    image_tag.short_description = 'Image'


class ProductRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    rating = models.IntegerField(default=1, validators=[MaxValueValidator(5), MinValueValidator(1)])
    review = models.TextField(max_length=2000, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)

