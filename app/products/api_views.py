from rest_framework.generics import ListAPIView, CreateAPIView
from .serializers import ProductSerializer, ProductImageSerializer
from .models import Product, ProductImage, Subdepartment, Department, Category, Brand
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect


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


class ProductDepartmentDetail2(ListAPIView):
    queryset = Product.objects.all()
    lookup_fields = 'department'
    serializer_class = ProductSerializer

    def get_queryset(self):
        dep = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields])
        if dep is None:
            return super().get_queryset()
        queryset = self.queryset.filter(department=dep.id)
        return queryset


class ProductSubdepartmentDetail(ListAPIView):
    queryset = Product.objects.all()
    lookup_fields = ['department', 'subdepartment']
    serializer_class = ProductSerializer

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

    def get_queryset(self):
        dep = get_object_or_404(Department, slug=self.kwargs[self.lookup_fields[0]])
        subdep = get_object_or_404(Subdepartment, slug=self.kwargs[self.lookup_fields[1]])
        cat = get_object_or_404(Category, slug=self.kwargs[self.lookup_fields[2]])
        if dep is None or subdep is None or cat is None:
            return 0
        queryset = self.queryset.filter(department=dep.id, subdepartment=subdep.id, category=cat.id)
        return queryset

