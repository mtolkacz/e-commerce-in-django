import logging

from django.conf import settings
from django.db import IntegrityError
from celery import shared_task

from gallop.celery import app
from cart.models import Shipment
from cart.functions import get_saved_carts, saved_carts_email

logger = logging.getLogger(__name__)


@app.task
def save_payment_object(payment, retries=0):
    try:
        payment.save()
        print("DJANGOTEST: save")
        order_id = payment.order.id
        print("DJANGOTEST: save payment order_id {}".format(order_id))
    except IntegrityError as ex:
        if retries < settings.DB_INTEGRITY_RETRIES:
            if payment:
                logger.error('Problem during saving payment: {}'.format(payment.id))
            else:
                logger.error('Problem during saving payment. No payment ID available.')
            save_payment_object.apply_async((payment, retries + 1), countdown=settings.INTEGRITY_RETRY_BACKOFF)
        else:
            raise ex
    else:
        try:
            shipment = Shipment.objects.get(order__id=order_id)
        except Shipment.DoesNotExist:
            logger.error("Can't find shipment after payment for order {}".format(order_id))
        else:
            shipment.status = Shipment.IN_PREPARATION
            try:
                shipment.save(update_fields=['status'], )
            except IntegrityError as ex:
                logger.error('Problem during saving shipment after payment: {}'.format(shipment.id))


@shared_task(bind=True, name='cart_reminder', max_retries=3, soft_time_limit=20)
def cart_reminder(self):
    orders = get_saved_carts()
    if orders:
        for order in orders:
            saved_carts_email(order)

