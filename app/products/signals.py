from .discount import DiscountManager


def discount_post_save(sender, instance, signal, *args, **kwargs):
    discount = DiscountManager()
    success = discount.calculate_discount(instance)

    if success:
        print('DJANGOTEST: Success, {}'.format(instance.id))
    else:
        # add celery task to calculate and to close discount at enddate
        print('DJANGOTEST: Failed, {}'.format(instance.id))



