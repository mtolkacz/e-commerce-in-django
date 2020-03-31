from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('add_item/', add_item_to_cart, name='add_item_to_cart'),
    # re_path('^add_item/(?P<item_id>[-\w]+)/$', add_item_to_cart, name='add_item_to_cart'),
    # re_path('^item/delete/(?P<item_id>[-\w]+)/$', delete_from_cart, name='delete_from_cart'),
    path('order-summary/', order_summary, name='order_summary'),
    path('', checkout, name='checkout'),
    # re_path('^payment/(?P<cart_id>[-\w]+)/$', process_payment, name='process_payment'),
    re_path('^update-transaction/(?P<cart_id>[-\w]+)/$', update_transaction_records, name='update_records'),
    path('success/', success, name='success'),
    path('calculate/', calculate_item_in_cart, name='calculate_item_in_cart'),
    path('delete_item/', delete_item_from_cart, name='delete_item_from_cart'),
]
