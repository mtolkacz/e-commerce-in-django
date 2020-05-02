from .discount import DiscountManager
from django.core.exceptions import ValidationError


def discount_post_save(sender, instance, signal, *args, **kwargs):
    # pass
    discount = DiscountManager(instance)
    discount_can_be_processed = discount.check_if_can_be_processed()

    if discount_can_be_processed:
        discount.process()
        print('DJANGOTEST: Calculated, {}'.format(instance.id))
    else:
        # add celery task to calculate and to close discount at enddate
        print('DJANGOTEST: Failed, {}'.format(instance.id))


def discount_pre_save(sender, instance, signal, *args, **kwargs):
    pass



