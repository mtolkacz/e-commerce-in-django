from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import *

handler404 = 'gallop.views.handler404'

urlpatterns = [
    path('', index, name='index'),
    path('products/', include('products.urls'), name='products'),
    path('blog/', include('blog.urls')),
    path('comments/', include('comments.urls')),
    path('gallop-admin/', admin.site.urls),
    path('purchase/', include('cart.urls')),
    path('account/', include('accounts.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('search/', search, name='search'),
]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
