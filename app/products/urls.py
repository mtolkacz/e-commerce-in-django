from django.urls import path
from . import views
from .api_views import *

from .views import ProductDetailView_old


urlpatterns = [
    path('browse/<str:department>/',
         ProductDepartmentDetail.as_view(),
         name='department'),

    path('browse/<str:department>/<str:subdepartment>/',
         ProductSubdepartmentDetail.as_view(),
         name='subdepartment'),

    path('browse/<str:department>/<str:subdepartment>/<str:category>/',
         ProductCategoryDetail.as_view(),
         name='category'),
    # todo change ProductDetailView to API
    path('product/<int:pk>-<str:slug>/', ProductDetailView_old.as_view(), name='product'),
]

# path('<str:department>/<str:subdepartment>/<str:category>/<int:pk>-<str:slug>/',
#      ProductDetailView.as_view(),
#      name='product'),
