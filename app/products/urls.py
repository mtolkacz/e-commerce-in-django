from django.urls import path
from . import views
from .views import Show


urlpatterns = [
    path('add', views.add, name='add'),
]
