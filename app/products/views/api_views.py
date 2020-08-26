import logging
import math
from decimal import Decimal

from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (CharFilter, DjangoFilterBackend,
                                           FilterSet, RangeFilter)
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from accounts.utils import get_user_object
from cart.models import OrderItem
from cart import utils
from gallop.utils import get_popular_products
from products.models import (Brand, Category, Department, LastViewedProducts,
                             Product, ProductImage, Subdepartment)
from products.serializers import (BrandSerializer, CategorySerializer,
                                  DepartmentSerializer, ProductSerializer,
                                  SubdepartmentSerializer)


logger = logging.getLogger(__name__)


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
    discountonly = CharFilter(method='get_discounted_products_only')

    class Meta:
        model = Product
        fields = ['price', 'brand']

    def get_brand_parameters(self, queryset, name, value):
        brands = self.request.GET.getlist('brand')
        return queryset.filter(brand__slug__in=brands)

    def get_discounted_products_only(self, queryset, name, value):
        return queryset.exclude(discounted_price__isnull=True)


class ProductCategoryDetail(ListAPIView):
    lookup_fields = ['department', 'subdepartment', 'category']
    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'products/shop_category.html'
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter,)
    filter_class = ProductFilter
    filterset_fields = ['price', 'brand', ]
    ordering_fields = ['price', 'creationdate', 'rating', ]
    pagination_class = PageNumberPagination
    department = None
    subdepartment = None
    category = None

    def get_product_hierarchy(self):
        try:
            self.department = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
            self.subdepartment = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
            self.category = get_object_or_404(Category, slug=self.kwargs[self.lookup_fields[2]])
        except(Department.DoesNotExist, Subdepartment.DoesNotExist, Category.DoesNotExist):
            pass
        else:
            return True

    def get_queryset(self, **kwargs):
        queryset = Product.objects.filter(department=self.department.id,
                                          subdepartment=self.subdepartment.id,
                                          category=self.category.id)
        return queryset

    def get_additional_data(self, request, queryset, **kwargs):
        distinct_brands = queryset.values('brand').distinct()
        brands = Brand.objects.filter(id__in=distinct_brands).order_by('name')
        dep = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
        subdep = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
        cat = get_object_or_404(Category, slug=self.kwargs[self.lookup_fields[2]])
        additional = {}
        if queryset:
            additional = {'brands': BrandSerializer(brands, many=True).data,
                          'page': int(request.GET.get('page', '1')), }
            min = queryset.order_by('price')[0].price
            max = queryset.order_by('-price')[0].price
            price = {
                'max': math.ceil(max.amount),
                'min': math.floor(min.amount),
            }
            additional['price'] = price
        additional['department'] = DepartmentSerializer(dep).data
        additional['subdepartment'] = SubdepartmentSerializer(subdep).data
        additional['category'] = CategorySerializer(cat).data
        return additional

    def append_data_after_filtering(self, request, additional, filtered_queryset):
        price_min = request.GET.get('price_min', False)
        price_max = request.GET.get('price_max', False)

        if price_min or price_max:
            filtered_price = {
                'max': Decimal(price_max),
                'min': Decimal(price_min),
            }
            additional['filtered_price'] = filtered_price

        if not filtered_queryset:
            # uncomment when more products
            # subdepartment = {'area': 'subdepartment', 'object': self.subdepartment}
            # popular_products = get_popular_products(where=subdepartment)
            popular_products = get_popular_products()
            serialized_products = self.get_serializer(popular_products, many=True)
            additional['popular_products'] = serialized_products.data
        return additional

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset(**kwargs)
        additional = self.get_additional_data(request, queryset, **kwargs)
        filtered_queryset = self.filter_queryset(queryset)

        # get filtered min and max price after filtering
        # and if filtered queryset is empty then get popular products
        additional = self.append_data_after_filtering(request, additional, filtered_queryset)

        page = self.paginate_queryset(filtered_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = {
                'objects': serializer.data,
                'additional': additional,
                # below counters are used to constraint frontend view on page template
                'filter_query_count': filtered_queryset.count() if filtered_queryset else 0,
                'query_count': queryset.count() if queryset else 0,
            }
            return self.get_paginated_response(data)

        serializer = self.get_serializer(filtered_queryset, many=True)
        data = {
            'objects': serializer.data,
            'additional': additional,
            'filter_query_count': filtered_queryset.count() if filtered_queryset else 0,
            'query_count': queryset.count() if queryset else 0,
        }
        return Response(data)

    def get(self, request, *args, **kwargs):
        if self.get_product_hierarchy():  # will raise 404 if url not correct
            return self.list(request, *args, **kwargs)
        else:
            raise Http404


class ProductDetail(ListAPIView):
    lookup_fields = ['department', 'subdepartment', 'category', 'pk', 'slug', ]
    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'products/product.html'
    department = None
    subdepartment = None
    category = None
    product = None

    def get_product_hierarchy(self):
        try:
            self.department = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
            self.subdepartment = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
            self.category = get_object_or_404(Category, slug=self.kwargs[self.lookup_fields[2]])
            self.product = get_object_or_404(Product,
                                             pk=self.kwargs[self.lookup_fields[3]],
                                             slug=self.kwargs[self.lookup_fields[4]])
        except(Department.DoesNotExist, Subdepartment.DoesNotExist, Category.DoesNotExist, Product.DoesNotExist):
            pass
        else:
            return True

    @staticmethod
    def check_if_exist_in_cart(request, prod):
        result = None
        cart = utils.get_pending_cart(request)
        try:
            result = OrderItem.objects.get(order=cart, product=prod).id if cart else False
        except OrderItem.DoesNotExist:
            pass
        return result

    def add_product_to_viewed(self, user):
        try:
            already_reviewed = LastViewedProducts.objects.get(product=self.product, user=user)
        except LastViewedProducts.DoesNotExist:
            already_reviewed = None
        if not already_reviewed:
            new_review = LastViewedProducts(product=self.product, user=user)
            new_review.save()

    def get(self, request, *args, **kwargs):
        if not self.get_product_hierarchy():
            raise Http404
        else:
            images = ProductImage.objects.filter(product=self.product)

            favorite = None
            if request.user.is_authenticated:
                user = get_user_object(request)
                favorite = self.product.check_if_favorite(user)
                self.add_product_to_viewed(user)

            exist_in_cart = self.check_if_exist_in_cart(request, self.product)
            context = {
                'object': self.product,
                'images': images,
                'exists_in_cart': exist_in_cart,
                'favorite': favorite,
            }
            return Response(context)
