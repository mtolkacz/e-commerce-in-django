from django.urls import path, re_path
from .views import *

urlpatterns = [
    # re_path('^add_item/(?P<item_id>[-\w]+)/$', add_item_to_cart, name='add_item_to_cart'),
    # re_path('^item/delete/(?P<item_id>[-\w]+)/$', delete_from_cart, name='delete_from_cart'),
    path('order-summary/', order_summary, name='order_summary'),
    path('cart', cart, name='cart'),
    path('cart/add_item/', add_item_to_cart, name='add_item_to_cart'),
    path('cart/calculate/', calculate_item_in_cart, name='calculate_item_in_cart'),
    path('cart/delete_item/', delete_item_from_cart, name='delete_item_from_cart'),
    path('cart/delete_cart/', delete_cart, name='delete_cart'),
    path('get_access/', get_access, name='get_access'),
    path('delete/', delete_purchase, name='delete_purchase'),
    path('checkout', checkout, name='checkout'),
    re_path('^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<oidb64>[0-9A-Za-z_\-]+)/$', purchase_activate, name='purchase_activate'),
    path('summary/<str:ref_code>/<str:oidb64>/', summary, name='summary'),
    re_path('^update-transaction/(?P<cart_id>[-\w]+)/$', update_transaction_records, name='update_records'),
    path('success/', success, name='success'),
    path('payment_done', payment_done, name='payment_done'),
    path('payment_cancelled', payment_cancelled, name='payment_cancelled'),
    path('process_payment', process_payment, name='process_payment'),
]
