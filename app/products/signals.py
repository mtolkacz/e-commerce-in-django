from .discount import DiscountManager
from django.core.exceptions import ValidationError
import logging
from .tasks import finish_discount, process_discount

logger = logging.getLevelName(__name__)


def discount_post_save(sender, instance, signal, *args, **kwargs):
    discount = DiscountManager(instance)
    discount_can_be_processed = discount.check_if_can_be_processed()

    # CELERY: Run product discount processing after 2 seconds if can be processed
    # or add task to run at the discount start date
    process_discount.apply_async([instance.id], countdown=2) \
        if discount_can_be_processed else process_discount.apply_async([instance.id], eta=instance.startdate)

    # CELERY: Add task to run discount finish method at the discount end date
    finish_discount.apply_async([instance.id], eta=instance.enddate)


def discount_pre_save(sender, instance, signal, *args, **kwargs):
    pass



