from django.urls import path

from .views import ajax

urlpatterns = [

    # Ajax request
    path('add/', ajax.add, name='add_comment'),
]
