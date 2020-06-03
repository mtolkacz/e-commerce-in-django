from django.urls import path, re_path

from . import ajax, views

urlpatterns = [
    # Standard django views
    path('cart', views.cart, name='cart'),
    path('checkout', views.checkout, name='checkout'),
    re_path('^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<oidb64>[0-9A-Za-z_\-]+)/$', views.purchase_activate, name='purchase_activate'),
    path('summary/<str:ref_code>/<str:oidb64>/', views.summary, name='summary'),

    # Ajax requests
    path('cart/add_item/', ajax.add_item_to_cart, name='add_item_to_cart'),
    path('cart/calculate/', ajax.calculate_item_in_cart, name='calculate_item_in_cart'),
    path('cart/delete_item/', ajax.delete_item_from_cart, name='delete_item_from_cart'),
    path('get_access/', ajax.get_access, name='get_access'),
    path('delete/', ajax.delete_purchase, name='delete_purchase'),
    path('checkout/process_promo_code/', ajax.process_promo_code, name='process_promo_code'),
    path('checkout/delete_promo_code/', ajax.delete_promo_code, name='delete_promo_code'),
    path('process_payment/', ajax.process_payment, name='process_payment'),
]
