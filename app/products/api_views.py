from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework import viewsets
from rest_framework.views import APIView
from .serializers import ProductSerializer, ProductImageSerializer
from .models import Product, ProductImage, Subdepartment, Department, Category
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


# class ProductDetail(RetrieveUpdateDestroyAPIView):
#     template_name = 'products/product_api.html'
#     renderer_classes = [TemplateHTMLRenderer]
#     serializer_class = ProductSerializer
#
#     def get(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         serializer = ProductSerializer(product)
#         return Response({'serializer': serializer, 'object': product})

    # def post(self, request, pk):
    #     return render(request, 'checkout.html')


class MultipleFieldLookupMixin(object):

    def get_objects(self):
        queryset = self.queryset            # Get the base queryset
        filter = {}
        # print('DJANGOTEST:  self.lookup_fields {}'.format(self.lookup_fields))
        for key, value in self.kwargs.items():
            print('DJANGOTEST:  key {}, lookup {}, value {}'.format(key, self.lookup_fields[key], value))
            obj = get_object_or_404(self.lookup_fields[key], slug=value)
            filter[key] = obj.id
        # for key, value in self.lookup_fields.items():
        #     print('DJANGOTEST: filter[0] {}, filter[1] {}, self.kwargs[key] {}'.format(key, value))
        #     if key in self.kwargs:
        #         if self.kwargs[key]:  # Ignore empty fields.
        #             obj = get_object_or_404(value, slug=self.kwargs[key])
        #             filter[key] = obj.id
        # print('DJANGOTEST: filter {}'.format(filter))
        queryset = self.queryset.filter(**filter)
        # self.check_object_permissions(self.request, obj)
        return queryset

    # todo filter version of get objects and with check_object_permissions
    # def get_objects(self):
    #     queryset = self.get_queryset()             # Get the base queryset
    #     queryset = self.filter_queryset(queryset)  # Apply any filter backends
    #     filter = {}
    #     for field in self.lookup_fields:
    #         if self.kwargs[field]: # Ignore empty fields.
    #             filter[field] = self.kwargs[field]
    #     obj = get_object_or_404(queryset, **filter)  # Lookup the object
    #     self.check_object_permissions(self.request, obj)
    #     return obj


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

