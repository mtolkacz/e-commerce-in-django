from rest_framework import serializers
from .models import Product, ProductImage, Department, Category, Subdepartment, Brand


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'slug')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name')


class SubdepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subdepartment
        fields = ('id', 'name', 'slug')


class ProductSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer()
    subdepartment = SubdepartmentSerializer()
    category = CategorySerializer()
    brand = BrandSerializer()

    class Meta:
        model = Product
        fields = ('id', 'short_name', 'name', 'description', 'price',
                  'thumbnail', 'slug', 'department', 'subdepartment', 'category', 'brand')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', )
