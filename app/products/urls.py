from django.urls import path
from . import views
from .api_views import *

from .views import ProductDetailView


urlpatterns = [
    path('api/product/', ProductList.as_view()),
    path('api/product/new', ProductCreate.as_view()),
    path('api/product/<int:id>/', ProductRetrieveUpdateDestroy.as_view()),
    path('api/products/<int:pk>/', ProductDetail.as_view()),
    path('api/image/', ProductImageList.as_view()),
    path('add', views.add, name='add'),
    path('<int:pk>-<str:slug>/', ProductDetailView.as_view(), name='product')
]
