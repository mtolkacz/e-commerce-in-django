from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price',
                  'department', 'subdepartment', 'category', 'thumbnail', )

    # override to
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['product_image'] = instance.show_images()
        data['current_price'] = instance.current_price()
        return data

