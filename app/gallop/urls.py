from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import *
import debug_toolbar
from django.conf import settings


handler404 = 'gallop.views.handler404'

urlpatterns = [
    path('', index, name='index'),
    path('products/', include('products.urls'), name='products'),
    path('blog/', include('blog.urls')),
    path('gallop-admin/', admin.site.urls),
    path('purchase/', include('cart.urls')),
    path('account/', include('accounts.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('paypal/', include('paypal.standard.ipn.urls')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns

# todo do I need this?
# if bool(settings.DEBUG):
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
