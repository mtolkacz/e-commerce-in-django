import logging

from django.conf import settings
from django.db import IntegrityError
from gallop.celery import app
from cart.models import Shipment

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

