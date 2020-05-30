from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('order-summary/', order_summary, name='order_summary'),
    path('cart', cart, name='cart'),
    path('cart/add_item/', add_item_to_cart, name='add_item_to_cart'),
    path('cart/calculate/', calculate_item_in_cart, name='calculate_item_in_cart'),
    path('cart/delete_item/', delete_item_from_cart, name='delete_item_from_cart'),
    path('get_access/', get_access, name='get_access'),
    path('delete/', delete_purchase, name='delete_purchase'),
    path('checkout', checkout, name='checkout'),
    path('checkout/process_promo_code/', process_promo_code, name='process_promo_code'),
    re_path('^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<oidb64>[0-9A-Za-z_\-]+)/$', purchase_activate, name='purchase_activate'),
    path('summary/<str:ref_code>/<str:oidb64>/', summary, name='summary'),
    path('process_payment/', process_payment, name='process_payment'),
]
