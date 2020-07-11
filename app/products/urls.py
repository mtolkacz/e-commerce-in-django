from django.urls import path

from .views import ajax, api_views

urlpatterns = [
    path('api/<str:department>/',
         api_views.ProductDepartmentDetail.as_view(),
         name='department'),

    path('api/<str:department>/<str:subdepartment>/',
         api_views.ProductSubdepartmentDetail.as_view(),
         name='subdepartment'),

    path('api/<str:department>/<str:subdepartment>/<str:category>/',
         api_views.ProductCategoryDetail.as_view(),
         name='category'),

    path('api/<str:department>/<str:subdepartment>/<str:category>/<int:pk>-<str:slug>/',
         api_views.ProductDetail.as_view(), name='product'),

    # Ajax request
    path('rate/', ajax.rating, name='rating')

]
