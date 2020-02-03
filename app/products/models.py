from django.db import models
from djmoney.models.fields import MoneyField
from django.utils.html import mark_safe


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


class Product(models.Model):
    name = models.CharField(max_length=100, default='New product')
    description = models.CharField(max_length=300, null=True)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.PROTECT, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    image = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image)

    image_tag.short_description = 'Image'

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Product name: ' + self.name + \
               ', Description: ' + self.description + \
               ', Price: ' + str(self.price) + \
               ', Category: ' + str(self.category) + \
               ', Image: ' + str(self.image)

