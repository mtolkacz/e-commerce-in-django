import logging
import sys
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError
from paypalcheckoutsdk.core import SandboxEnvironment, PayPalHttpClient
from paypalcheckoutsdk.orders import OrdersGetRequest

from cart.models import Payment

logger = logging.getLogger(__name__)


class PayPalClient:
    def __init__(self):
        self.client_id = settings.PAYPAL_API_KEY[0]
        self.client_secret = settings.PAYPAL_SECRET[0]

        """Set up and return PayPal Python SDK environment with PayPal access credentials.
           This sample uses SandboxEnvironment. In production, use LiveEnvironment."""

        self.environment = SandboxEnvironment(client_id=self.client_id, client_secret=self.client_secret)

        """ Returns PayPal HTTP client instance with environment that has access
            credentials context. Use this instance to invoke PayPal APIs, provided the
            credentials have access. """
        self.client = PayPalHttpClient(self.environment)

    def object_to_json(self, json_data):
        """
        Function to print all json data in an organized readable manner
        """
        result = {}
        if sys.version_info[0] < 3:
            itr = json_data.__dict__.iteritems()
        else:
            itr = json_data.__dict__.items()
        for key, value in itr:
            # Skip internal attributes.
            if key.startswith("__"):
                continue
            result[key] = self.array_to_json_array(value) if isinstance(value, list) else \
                self.object_to_json(value) if not self.is_primittive(value) else value
        return result

    def array_to_json_array(self, json_array):
        result = []
        if isinstance(json_array, list):
            for item in json_array:
                result.append(self.object_to_json(item) if not self.is_primittive(item)
                              else self.array_to_json_array(item) if isinstance(item, list) else item)
        return result

    # def is_primittive(self, data):
    #     return isinstance(data, str) or isinstance(data, unicode) or isinstance(data, int)


class PaypalManager(PayPalClient):
    def __init__(self, payment_details):
        super().__init__()
        self.details = payment_details

    def get_create_date(self):
        try:
            create_time = parser.parse(self.details['create_time'])
        except KeyError:
            create_time = None
        return create_time

    def get_update_date(self):
        try:
            update_time = parser.parse(self.details['update_time'])
        except KeyError:
            update_time = None
        return update_time

    def get_id(self):
        try:
            payment_id = self.details['id']
        except KeyError:
            payment_id = None
        return payment_id

    def confirm_payment(self):
        try:
            order_id = self.details['id']
        except KeyError:
            order_id = None
        if order_id:
            request = OrdersGetRequest(order_id)
            response = self.client.execute(request)
            return response.result.id

    def get_value(self):
        try:
            amount_value = self.details['purchase_units'][0]['amount']['value']
        except KeyError:
            amount_value = None
        try:
            currency = self.details['purchase_units'][0]['amount']['currency_code']
        except KeyError:
            currency = None
        return Money(Decimal(amount_value), currency) if amount_value and currency else None

    def get_status(self):
        try:
            status = self.details['status']
        except KeyError:
            status = None
        return status

    def get_payer_id(self):
        try:
            payer_id = self.details['payer']['payer_id']
        except KeyError:
            payer_id = None
        return payer_id

    def get_payer_email(self):
        try:
            payer_email = self.details['payer']['email_address']
        except KeyError:
            payer_email = None
        return payer_email

    def get_payer_surname(self):
        try:
            payer_surname = self.details['payer']['name']['surname']
        except KeyError:
            payer_surname = None
        return payer_surname

    def get_payer_given_name(self):
        try:
            given_name = self.details['payer']['name']['given_name']
        except KeyError:
            given_name = None
        return given_name

    # def update_shipment(self):
    #     try:
    #         shipment = Shipment.objects.get(order__id=order_id)
    #     except Shipment.DoesNotExist:
    #         logger.error("Can't find shipment after payment for order {}".format(order_id))
    #     else:
    #         shipment.status = Shipment.IN_PREPARATION
    #         try:
    #             shipment.save(update_fields=['status'], )
    #         except IntegrityError as ex:
    #             logger.error('Problem during saving shipment after payment: {}'.format(shipment.id))

    def create_payment(self, order):
        paypal_payment_id = self.get_id()
        payment = Payment(id=paypal_payment_id,
                          order=order,
                          createdate=self.get_create_date(),
                          updatedate=self.get_update_date(),
                          status=self.get_status(),
                          value=self.get_value(),
                          payer_id=self.get_payer_id(),
                          email=self.get_payer_email(),
                          given_name=self.get_payer_given_name(),
                          surname=self.get_payer_surname())
        try:
            payment.save()
        except IntegrityError as ex:
           logger.error('Problem during saving payment: {}'.format(paypal_payment_id))
           payment = None
        return payment if payment else False