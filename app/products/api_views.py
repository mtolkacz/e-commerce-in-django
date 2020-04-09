from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework import viewsets
from rest_framework.views import APIView
from .serializers import ProductSerializer, ProductImageSerializer
from .models import Product, ProductImage
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.http import HttpResponse


class ProductPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class ProductList(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('id', )
    search_fields = ('name', 'description',)
    pagination_class = ProductPagination

    # todo Example of filtering API - testing
    def get_queryset(self):
        price = self.request.query_params.get('price', None)
        if price is None:
            return super().get_queryset()
        queryset = Product.objects.all()
        if price.lower() == 'true':
            return queryset.filter(
                price__gte='300',
            )
        else:
            return queryset.filter(
                price__lt='300',
            )
        return queryset


class ProductImageList(ListAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_fields = ('product', )


class ProductCreate(CreateAPIView):
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        try:
            price = request.data.get('price')
            if price is not None and float(price) <= 0.0:
                raise ValidationError({'price': 'Must be above 0.00'})
        except ValueError:
            raise ValidationError({'price': 'A valid number is required'})
        return super().create(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return redirect('checkout')


class ProductDetail(RetrieveUpdateDestroyAPIView):
    template_name = 'products/product_api.html'
    renderer_classes = [TemplateHTMLRenderer]
    serializer_class = ProductSerializer

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response({'serializer': serializer, 'object': product})

    # def post(self, request, pk):
    #     return render(request, 'checkout.html')


class ProductRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    lookup_field = 'id'
    serializer_class = ProductSerializer

    def delete(self, request, *args, **kwargs):
        product_id = request.data.get('id')
        response = super().delete(request, *args, **kwargs)
        if response.status_code == 204:  # 204 - No Content -
            from django.core.cache import cache
            cache.delete('product_data_{}'.format(product_id))
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:  # 200 - OK
            from django.core.cache import cache
            product = response.data
            cache.set('product_data_{}'.format(product['id']),
                      {'name': product['name'],
                       'brand': product['brand'],
                       'description': product['description'],
                       'price': product['price'],
                       'department': product['department'],
                       'subdepartment': product['subdepartment'],
                       'category': product['category'],
                       'thumbnail': product['thumbnail'],
                       })
            return response


