from django.utils import timezone


def shipment_pre_save(sender, instance, signal, *args, **kwargs):
    now = timezone.now()
    if instance.status == instance.IN_PREPARATION:
        instance.preparationdate = now
    elif instance.status == instance.SENT:
        instance.sentdate = now
    elif instance.status == instance.DELIVERED:
        instance.delivereddate = now


def order_pre_delete(sender, instance, signal, *args, **kwargs):
    items = instance.items.all()
    for item in items:
        if instance.status == instance.BOOKED:
            if item.booked:
                item.product.undo_book()
        item.delete()
