from datetime import datetime
from decimal import *

from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import signals
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.text import slugify
from djmoney.models.fields import MoneyField

from accounts.models import User

from .signals import discount_post_save, discount_pre_save
from .validators import ProductIDsValidator


class Department(models.Model):
    name = models.CharField(max_length=100, default="No department")
    slug = models.SlugField(max_length=100)
    image1 = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')
    image2 = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag1(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image1)

    def image_tag2(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image2)

    image_tag1.short_description = 'Image1'
    image_tag2.short_description = 'Image2'

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)


class Subdepartment(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=100, default="No subdepartment")
    slug = models.SlugField(max_length=100)
    image1 = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')
    image2 = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag1(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image1)

    def image_tag2(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image2)

    image_tag1.short_description = 'Image1'
    image_tag2.short_description = 'Image2'

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name

    def get_categories(self):
        return Category.objects.filter(subdepartment=self.id).distinct('name').order_by('name')

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)


class Category(models.Model):
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.PROTECT, null=True, related_name="sub")
    name = models.CharField(max_length=100, default="No category")
    slug = models.SlugField(max_length=100)
    image1 = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')
    image2 = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag1(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image1)

    def image_tag2(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image2)

    image_tag1.short_description = 'Image1'
    image_tag2.short_description = 'Image2'

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100)
    image1 = models.ImageField(upload_to='pic_folder/brands/', default='pic_folder/None/no-img.jpg')

    def image_tag1(self):
        return mark_safe('<img src="/media/%s" width="160" height="80" />' % self.image1)

    image_tag1.short_description = 'Image1'

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(models.Model):
    short_name = models.CharField(max_length=50, default='Short product name')
    name = models.CharField(max_length=150, default='Product name')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True)
    description = RichTextField()
    price = MoneyField(max_digits=6, decimal_places=2, default_currency='USD', null=False)
    discounted_price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', editable=False, null=True,
                                  blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.PROTECT, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    thumbnail = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')
    slug = models.SlugField(max_length=150)  # todo check max product name length
    stock = models.SmallIntegerField(default=0, null=False)
    booked = models.PositiveSmallIntegerField(default=0, null=False)
    creationdate = models.DateTimeField(auto_now_add=True)

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.thumbnail)

    image_tag.short_description = 'Image'

    def get_price_in_string(self):
        return str(self.price)

    def book(self, amount=0):
        if amount > 0:
            self.booked += amount
            self.stock -= amount
        else:
            self.booked += 1
            self.stock -= 1
        self.save(update_fields=['booked', 'stock'])

    def undo_book(self):
        if self.booked > 0:
            self.booked -= 1
            self.stock += 1
            self.save(update_fields=['booked', 'stock'])
            return True
        else:
            return False

    def add_stock(self):
        self.stock += 1
        self.save(update_fields=['stock'])

    def remove_stock(self):
        if self.stock > 0:
            self.stock -= 1
            self.save(update_fields=['stock'])

    def get_discounted_price_in_string(self):
        return str(self.discounted_price) if self.discounted_price else ''

    def get_discount_value(self):
        if self.discounted_price:
            try:
                discount_line = DiscountLine.objects.get(product=self, status=DiscountLine.ACTIVE)
            except DiscountLine.DoesNotExist:
                return ''
            else:
                return discount_line.discount.value

    def reset_price(self):
        if self.discounted_price is not None:
            self.discounted_price = None
            self.save(update_fields=['discounted_price'])

    def get_discounted_price(self, discount_value):
        if isinstance(discount_value, int):
            return Decimal(((100 - discount_value) * self.price.amount) / 100)
        else:
            return False

    def get_absolute_url(self):
        return reverse('product',
                       kwargs={
                           'department': self.department.slug,
                           'subdepartment': self.subdepartment.slug,
                           'category': self.category.slug,
                           'pk': self.pk,
                           'slug': self.slug, })

    def get_absolute_url_str(self):
        return str(reverse('product',
                           kwargs={
                               'department': self.department.slug,
                               'subdepartment': self.subdepartment.slug,
                               'category': self.category.slug,
                               'pk': self.pk,
                               'slug': self.slug, }))

    def get_add_to_cart_url(self):
        return reverse("add_item_to_cart", kwargs={
            'item_id': self.id
        })

    def save(self, *args, **kwargs):
        value = self.short_name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_first_image_url(self):
        return ProductImage.objects.filter(product=self).order_by('id')[0].image.url

    def __str__(self):
        return '{}, {}'.format(self.id, self.name)

    def check_if_favorite(self, user):
        try:
            fav = Favorites.objects.get(product=self, user=user)
        except Favorites.DoesNotExist:
            fav = False
        return True if fav else False

    def get_rate(self):
        try:
            values = ProductRating.objects.values_list('score', flat=True).get(product=self)
        except ProductRating.DoesNotExist:
            values = None
        values_list = [values] if values else None

        return sum(values_list) / len(values_list) if values_list else None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name="images")
    image = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image)

    image_tag.short_description = 'Image'


class ProductRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    score = models.PositiveSmallIntegerField(default=1, validators=[MaxValueValidator(5), MinValueValidator(1)])
    review = models.TextField(max_length=2000, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('product', 'user')


class Favorites(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    class Meta:
        unique_together = ('product', 'user')


class DiscountPriorityType(models.Model):
    name = models.CharField(max_length=150, default='Priority name', blank=True)
    value = models.IntegerField(default=100, validators=[MaxValueValidator(100), MinValueValidator(1)])
    description = models.CharField(max_length=300, null=True, blank=True)

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name


class DiscountType(models.Model):
    name = models.CharField(max_length=150, default='Discount type name', unique=True, blank=False)
    model = models.CharField(max_length=50, null=True, editable=False)
    lookup_field = models.CharField(max_length=50, null=True, editable=False)

    def __unicode__(self):
        return '%s' % self.name

    def __str__(self):
        return self.name


class Discount(models.Model):
    INACTIVE = 1
    ACTIVE = 2
    FINISHED = 3
    STATUS = (
        (INACTIVE, 'Inactive'),
        (ACTIVE, 'Active'),
        (FINISHED, 'Finished'),
    )
    name = models.CharField(max_length=150, default='Discount name', null=False, blank=False)
    type = models.ForeignKey(DiscountType, on_delete=models.PROTECT, null=False, blank=False)
    # e.g. id of department, subdepartment, category and other levels or None if global for all products
    set_id = models.IntegerField(null=False, blank=False, validators=[MinValueValidator(1)])
    value = models.IntegerField(null=False, validators=[MaxValueValidator(99), MinValueValidator(1)])
    startdate = models.DateTimeField(null=False, default=datetime(2020, 4, 17))
    # todo change default dates after adding unit tests
    enddate = models.DateTimeField(null=False, default=datetime(2020, 7, 17))
    description = models.CharField(max_length=300, null=True, blank=True)
    priority = models.ForeignKey(DiscountPriorityType, on_delete=models.PROTECT, null=False)
    status = models.PositiveSmallIntegerField(
        choices=STATUS,
        default=INACTIVE,
    )
    image = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status'])

    def get_top_products(self):
        ids = DiscountLine.objects.filter(discount=self).values_list('product', flat=True)
        return Product.objects.filter(id__in=ids)[:3]

    def clean(self):
        super().clean()

        # todo stop execution if already exists Discount/should we allow to edit already created Discount?
        try:
            already_exists = Discount.objects.get(id=self.id)
        except Discount.DoesNotExist:
            already_exists = None
        if already_exists:
            raise ValidationError('Cannot modify already created discount')
        if self.enddate <= self.startdate:
            raise ValidationError('End date must be greater than start date')
        if self.enddate <= timezone.now():
            raise ValidationError('End date must be greater than current datetime')

    def __str__(self):
        return '{}, {}'.format(self.id, self.name)


class DiscountProductList(models.Model):
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, null=False)
    ids = models.TextField(null=True)

    def get_product_list(self):
        return [int(x) for x in str(self.ids).split(';')]


class DiscountLine(models.Model):
    INACTIVE = 1
    ACTIVE = 2
    FINISHED = 3
    STATUS = (
        (INACTIVE, 'Inactive'),
        (ACTIVE, 'Active'),
        (FINISHED, 'Finished'),
    )
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    status = models.PositiveSmallIntegerField(
        choices=STATUS,
        default=INACTIVE,
    )

    def __str__(self):
        return '{}, {}, {}'.format(self.id, self.discount.name, self.product.name)

    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status'])


class DiscountCustom(models.Model):
    name = models.CharField(max_length=150, default='Custom product list', null=False, blank=False)
    value = models.TextField(null=False, validators=[ProductIDsValidator], blank=False)

    def clean(self):
        super().clean()
        list = str(self.value).split(';')
        if len(list) != len(set(list)):
            raise ValidationError('Product list contains duplicates!')

    def get_product_list(self):
        return str(self.value).split(';')

    def get_products_id(self):
        ids = [int(x) for x in self.get_product_list()]
        return ids


class LastViewedProducts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)


signals.pre_save.connect(discount_pre_save, sender=Discount)
signals.post_save.connect(discount_post_save, sender=Discount)
