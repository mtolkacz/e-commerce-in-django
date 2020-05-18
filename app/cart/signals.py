from django.utils import timezone


def shipment_pre_save(sender, instance, signal, *args, **kwargs):
    now = timezone.now()
    if instance.status == instance.IN_PREPARATION:
        instance.preparationdate = now
    elif instance.status == instance.SENT:
        instance.sentdate = now
    elif instance.status == instance.DELIVERED:
        instance.delivereddate = now