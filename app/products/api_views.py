from rest_framework.generics import ListAPIView
from .serializers import ProductSerializer, BrandSerializer, \
    DepartmentSerializer, SubdepartmentSerializer, CategorySerializer
from .models import Product, ProductImage, Subdepartment, Department, Category, Brand
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import math


class MultipleFieldLookupMixin(object):

    def get_objects(self):
        queryset = self.queryset            # Get the base queryset
        filter = {}
        for key, value in self.kwargs.items():
            obj = get_object_or_404(self.lookup_fields[key], slug=value)
            filter[key] = obj.id
        queryset = self.queryset.filter(**filter)
        return queryset


class ProductDetail(MultipleFieldLookupMixin, ListAPIView):
    queryset = Product.objects.all()
    lookup_fields = {'department': Department, 'subdepartment': Subdepartment, 'category': Category}
    serializer_class = ProductSerializer
    models = [Department, Subdepartment, Category]

    def get_queryset(self):
        self.queryset = self.get_objects()
        return self.queryset


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


class ProductCategoryDetail(ListAPIView):
    queryset = Product.objects.all()
    lookup_fields = ['department', 'subdepartment', 'category']
    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'products/shop_category.html'
    filter_backends = (SearchFilter, OrderingFilter)
    filterset_fields = ['price', ]
    ordering_fields = ['price', ]
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
                          'total_active_records': queryset.count(),
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset(**kwargs))

        additional = self.get_additional_data(request, queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = {
                'objects': serializer.data,
                'additional': additional,
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

    def get(self, request, *args, **kwargs):
        dep = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
        subdep = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
        cat = get_object_or_404(Category, slug=self.kwargs[self.lookup_fields[2]])
        prod = get_object_or_404(Product, id=self.kwargs[self.lookup_fields[3]])
        if dep is None or subdep is None or cat is None or prod is None:
            return 0
        object = get_object_or_404(Product, department=dep, subdepartment=subdep, category=cat, id=prod.id)
        images = ProductImage.objects.filter(product=object)
        context = {
            'object': object,
            'images': images,
        }
        return Response(context)

