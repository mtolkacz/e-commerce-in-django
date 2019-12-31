from django.urls import path, re_path
from .views import *

urlpatterns = [
    re_path('^add-to-cart/(?P<item_id>[-\w]+)/$', add_to_cart, name='add_to_cart'),
    re_path('^item/delete/(?P<item_id>[-\w]+)/$', delete_from_cart, name='delete_from_cart'),
    path('order-summary/', order_summary, name='order_summary'),
    path('', checkout, name='checkout'),
    # path('checkout/', checkout, name='checkout'),
    # re_path('^payment/(?P<cart_id>[-\w]+)/$', process_payment, name='process_payment'),
    re_path('^update-transaction/(?P<cart_id>[-\w]+)/$', update_transaction_records, name='update_records'),
    path('success/', success, name='success'),
]
