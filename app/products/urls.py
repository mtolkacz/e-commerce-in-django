from django.urls import path
from . import views
from .api_views import *

urlpatterns = [
    path('<str:department>/',
         ProductDepartmentDetail.as_view(),
         name='department'),

    path('<str:department>/<str:subdepartment>/',
         ProductSubdepartmentDetail.as_view(),
         name='subdepartment'),

    path('<str:department>/<str:subdepartment>/<str:category>/',
         ProductCategoryDetail.as_view(),
         name='category'),

    path('<str:department>/<str:subdepartment>/<str:category>/<int:pk>-<str:slug>/',
         ProductDetail.as_view(), name='product'),

]
