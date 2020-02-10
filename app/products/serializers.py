from rest_framework import serializers
from .models import Product, ProductImage


class ProductSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(read_only=True)
    department_name = serializers.CharField(max_length=100, read_only=True)
    subdepartment_name = serializers.CharField(max_length=100, read_only=True)
    category_name = serializers.CharField(max_length=100, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'brand', 'brand_name', 'name', 'description', 'price',
                  'thumbnail', 'department', 'department_name', 'subdepartment',
                  'subdepartment_name', 'category', 'category_name')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', )
