from django.urls import path
from . import views


urlpatterns = [
    path('', views.login, name='login'),
    path('login', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('successful/', views.successful_registration, name='successful_registration'),
]

#     path('register', views.register, name='register')
