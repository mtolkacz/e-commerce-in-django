from rest_framework import serializers
from .models import Product, ProductImage, Department, Category, Subdepartment, Brand


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'slug')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image1', 'image2')


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug')


class SubdepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subdepartment
        fields = ('id', 'name', 'slug')


class ProductSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer()
    subdepartment = SubdepartmentSerializer()
    category = CategorySerializer()
    brand = BrandSerializer()
    url = serializers.CharField(source='get_absolute_url')
    price = serializers.CharField(source='get_price_in_string')
    discount = serializers.CharField(source='get_discount_value')
    discounted_price = serializers.CharField(source='get_discounted_price_in_string')

    class Meta:
        model = Product
        fields = ('id', 'short_name', 'name', 'description', 'price', 'discounted_price', 'discount',
                  'thumbnail', 'slug', 'department', 'subdepartment', 'category', 'brand', 'url', 'stock')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', )
