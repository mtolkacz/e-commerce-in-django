from decimal import Decimal

from rest_framework.generics import ListAPIView
from .serializers import ProductSerializer, BrandSerializer, \
    DepartmentSerializer, SubdepartmentSerializer, CategorySerializer
from .models import Product, ProductImage, Subdepartment, Department, Category, Brand
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, RangeFilter
from django.shortcuts import get_object_or_404
import math


class ProductDepartmentDetail(ListAPIView):
    queryset = Product.objects.all()
    lookup_fields = 'department'
    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'products/department.html'

    def get(self, request, *args, **kwargs):
        department = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields])
        if department is None:
            return super().get_queryset()
        queryset = self.queryset.filter(department=department)
        serializer = ProductSerializer(queryset)
        subdepartments = Subdepartment.objects.filter(department=department)
        categories = Category.objects.filter(subdepartment__in=subdepartments)
        distinct_brands = queryset.values_list('brand', flat=True).distinct('brand')
        brands = Brand.objects.filter(id__in=distinct_brands).order_by('name')
        return Response({'serializer': serializer, 'objects': queryset, 'department': department,
                         'brands': brands, 'subdepartments': subdepartments, 'categories': categories})


class ProductSubdepartmentDetail(ListAPIView):
    queryset = Product.objects.all()
    lookup_fields = ['department', 'subdepartment']
    serializer_class = ProductSerializer
    ordering_fields = ['id']
    filter_backends = [OrderingFilter]

    def get_queryset(self):
        dep = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
        subdep = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
        if dep is None or subdep is None:
            return 0
        queryset = self.queryset.filter(department=dep.id, subdepartment=subdep.id)
        return queryset


class ProductFilter(FilterSet):
    price = RangeFilter()
    brand = CharFilter(method='get_brand_parameters')

    class Meta:
        model = Product
        fields = ['price', 'brand']

    def get_brand_parameters(self, queryset, name, value):
        brands = self.request.GET.getlist('brand')
        return queryset.filter(brand__slug__in=brands)


class ProductCategoryDetail(ListAPIView):
    queryset = Product.objects.all()
    lookup_fields = ['department', 'subdepartment', 'category']
    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'products/shop_category.html'
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter,)
    filter_class = ProductFilter
    filterset_fields = ['price', 'brand', ]
    ordering_fields = ['price', 'creationdate', 'rating', ]
    pagination_class = PageNumberPagination

    def get_queryset(self, **kwargs):
        dep = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
        subdep = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
        cat = get_object_or_404(Category, slug=self.kwargs[self.lookup_fields[2]])
        if dep is None or subdep is None or cat is None:
            return 0
        queryset = self.queryset.filter(department=dep.id, subdepartment=subdep.id, category=cat.id)
        return queryset

    def get_additional_data(self, request, queryset):
        distinct_brands = queryset.values('brand').distinct()
        brands = Brand.objects.filter(id__in=distinct_brands).order_by('name')
        additional = {}
        if queryset:
            product = queryset[0]
            additional = {'department': DepartmentSerializer(product.department).data,
                          'subdepartment': SubdepartmentSerializer(product.subdepartment).data,
                          'category': CategorySerializer(product.category).data,
                          'brands': BrandSerializer(brands, many=True).data,
                          'page': int(request.GET.get('page', '1'))}
            min = queryset.order_by('price')[0].price
            max = queryset.order_by('-price')[0].price
            price = {
                'max': math.ceil(max.amount),
                'min': math.floor(min.amount),
            }
            additional['price'] = price
        else:
            popular_products = self.get_serializer(self.queryset[:10], many=True)
            additional['popular_products'] = popular_products.data
        return additional

    @staticmethod
    def get_filtered_price(request, queryset, additional):
        price_min = request.GET.get('price_min', False)
        price_max = request.GET.get('price_max', False)

        if price_min or price_max:
            filtered_price = {
                'max': Decimal(price_max),
                'min': Decimal(price_min),
            }
            additional['filtered_price'] = filtered_price
        return additional

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset(**kwargs)
        additional = self.get_additional_data(request, queryset)
        queryset = self.filter_queryset(queryset)
        additional = self.get_filtered_price(request, queryset, additional)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = {
                'objects': serializer.data,
                'additional': additional,
                'query_count': queryset.count(),
            }
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = {
            'objects': serializer.data,
            'additional': additional.data,
        }
        return Response(data)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ProductDetail(ListAPIView):
    lookup_fields = ['department', 'subdepartment', 'category', 'pk']
    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'products/product.html'

    @staticmethod
    def check_if_exist_in_cart(request, prod):
        from cart.views import get_pending_cart
        from cart.models import OrderItem
        result = None
        cart = get_pending_cart(request)
        try:
            result = OrderItem.objects.get(order=cart, product=prod).id if cart else False
        except OrderItem.DoesNotExist:
            pass
        return result

    def get(self, request, *args, **kwargs):
        dep = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
        subdep = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
        cat = get_object_or_404(Category, slug=self.kwargs[self.lookup_fields[2]])
        prod = get_object_or_404(Product, id=self.kwargs[self.lookup_fields[3]])
        if dep is None or subdep is None or cat is None or prod is None:
            return 0
        object = get_object_or_404(Product, department=dep, subdepartment=subdep, category=cat, id=prod.id)
        images = ProductImage.objects.filter(product=object)

        exist_in_cart = self.check_if_exist_in_cart(request, prod)
        context = {
            'object': object,
            'images': images,
            'exists_in_cart': exist_in_cart,
        }
        return Response(context)

