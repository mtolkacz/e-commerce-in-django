from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', include('products.urls')),
    path('products/', include('products.urls')),
    path('blog/', include('blog.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('social-auth/', include('social_django.urls', namespace="social")),
]

if bool(settings.DEBUG):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
