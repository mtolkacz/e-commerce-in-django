from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('', login, name='login'),
    path('login', login, name='login'),
    path('test', test, name='test'),
    path('test2', test2, name='test2'),
    path('profile', profile, name='profile'),
    path('logout/', logout, name='logout'),
    path('successful/', successful_registration, name='successful_registration'),
    re_path('^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', activate,
            name='activate'),
]
