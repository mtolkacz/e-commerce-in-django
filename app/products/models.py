from django.db import models
from djmoney.models.fields import MoneyField
from django.utils.html import mark_safe
from django.core.validators import MaxValueValidator, MinValueValidator
from accounts.models import User
from ckeditor.fields import RichTextField
from django.shortcuts import reverse
from django.utils.text import slugify


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
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    subdepartment = models.ForeignKey(Subdepartment, on_delete=models.PROTECT, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    thumbnail = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')
    slug = models.SlugField(max_length=150)  # todo check max product name length

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.thumbnail)

    image_tag.short_description = 'Image'

    # todo to consider if need to add "get" to the below methods names

    def get_absolute_url(self):
        kwargs = {
            'pk': self.id,
            'slug': self.slug
        }
        return reverse("product", kwargs=kwargs)

    def get_add_to_cart_url(self):
        return reverse("add_item_to_cart", kwargs={
            'item_id': self.id
        })

    def save(self, *args, **kwargs):
        value = self.short_name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_images(self):
        return self.images[0]

    def get_first_image(self):
        return self.productimage_set.all()[0]

    def brand_name(self):
        return self.brand.name

    def department_name(self):
        return self.department.name

    def subdepartment_name(self):
        return self.subdepartment.name

    def category_name(self):
        return self.category.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Product name: ' + self.name + \
               ', Description: ' + self.description + \
               ', Price: ' + str(self.price) + \
               ', Category: ' + str(self.category) + \
               ', Image: ' + str(self.thumbnail)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name="images")
    image = models.ImageField(upload_to='pic_folder/', default='pic_folder/None/no-img.jpg')

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % self.image)

    image_tag.short_description = 'Image'


class ProductRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    rating = models.IntegerField(default=1, validators=[MaxValueValidator(5), MinValueValidator(1)])
    review = models.TextField(max_length=2000, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)

