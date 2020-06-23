from . import views
from django.urls import path

urlpatterns = [
    path('posts/', views.Posts.as_view(), name='posts'),
    # path('<slug:slug>/', views.PostDetail.as_view(), name='post_detail'),
    path('posts/<slug:slug>/', views.post_detail, name='post_detail'),
]
