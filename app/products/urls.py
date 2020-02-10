from django.urls import path
from . import views
from .api_views import *


urlpatterns = [
    path('api/product/', ProductList.as_view()),
    path('api/product/new', ProductCreate.as_view()),
    path('api/product/<int:id>/', ProductRetrieveUpdateDestroy.as_view()),
    path('api/image/', ProductImageList.as_view()),
    path('add', views.add, name='add'),
]
