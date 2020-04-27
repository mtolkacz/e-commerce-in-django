from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import *

handler404 = 'gallop.views.handler404'

urlpatterns = [
    path('', index, name='index'),
    path('', include('products.urls')),
    path('blog/', include('blog.urls')),
    path('admin/', admin.site.urls),
    path('cart/', include('cart.urls')),
    path('account/', include('accounts.urls')),
    path('social-auth/', include('social_django.urls', namespace="social")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# todo do I need this?
# if bool(settings.DEBUG):
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
