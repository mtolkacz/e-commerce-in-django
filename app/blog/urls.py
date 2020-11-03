from django.urls import path

from . import views

urlpatterns = [
    path('posts/', views.Posts.as_view(), name='posts'),
    path('posts/<slug:slug>/', views.post_detail, name='post_detail'),
]
