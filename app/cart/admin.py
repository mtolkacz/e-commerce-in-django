from django.contrib import admin
from django.db.models import OneToOneField, ForeignKey, ManyToOneRel

from .models import Shipment, ShipmentType, Order, OrderItem, Payment

MySpecialAdmin = lambda model: type('SubClass'+model.__name__, (admin.ModelAdmin,), {
    'list_display': [x.name for x in model._meta.fields],
    'list_select_related': [x.name for x in model._meta.fields if isinstance(x, (ManyToOneRel, ForeignKey, OneToOneField,))]
})

admin.site.register(Payment, MySpecialAdmin(Payment))
admin.site.register(Order, MySpecialAdmin(Order))
admin.site.register(OrderItem, MySpecialAdmin(OrderItem))
admin.site.register(Shipment, MySpecialAdmin(Shipment))
admin.site.register(ShipmentType, MySpecialAdmin(ShipmentType))
