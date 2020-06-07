from django.urls import path
from . import views
from .api_views import *
from . import ajax

urlpatterns = [
    path('api/<str:department>/',
         ProductDepartmentDetail.as_view(),
         name='department'),

    path('api/<str:department>/<str:subdepartment>/',
         ProductSubdepartmentDetail.as_view(),
         name='subdepartment'),

    path('api/<str:department>/<str:subdepartment>/<str:category>/',
         ProductCategoryDetail.as_view(),
         name='category'),

    path('api/<str:department>/<str:subdepartment>/<str:category>/<int:pk>-<str:slug>/',
         ProductDetail.as_view(), name='product'),

    # Ajax request
    path('rate/', ajax.rating, name='rating')

]
