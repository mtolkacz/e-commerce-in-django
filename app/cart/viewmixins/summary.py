from django.conf import settings
from django.contrib import messages
from django.contrib.sessions.models import Session

from cart.models import OrderAccess, Shipment, Payment, Order
from cart.utils import send_purchase_link


class SummaryContextMixing(object):
    # permission level
    NO_ACCESS = 1
    TEMP_ACCESS = 2
    USER_AUTHENTICATED = 3
    NEED_ACCESS_CODE = 4
    UNKNOWN_ERROR = None
    HAS_ACCESS = [TEMP_ACCESS, USER_AUTHENTICATED]

    # permission level description
    # Order has access_code and no owner = no user and need access for session
    # 	1 - render access key page - no access
    # 	2 - render summary if - has access
    # Is Owner and and no access key = get context for user
    # 	3 - render summary
    # No access key and no owner = generate key and sent to e-mail
    # 	4 - go to main page and report that link has been sent
    # Unknown error
    # 	None - go to main page reporting unknown error

    def __init__(self):
        self.request = None
        self.user = None
        self.ref_code = None
        self.oidb64 = None
        self.session = None
        self.context = {}
        self.order = None
        self.shipment = None
        self.access = None
        self.permission = None

    def get_user_session(self, request):
        session = request.session.session_key
        if not session:
            request.session['guest'] = True
            request.session.save()
        try:
            return Session.objects.get(session_key=request.session.session_key)
        except Session.DoesNotExist:
            pass

    def get_access_object(self):
        if self.session:
            try:
                return OrderAccess.objects.get(session_key=self.session)
            except OrderAccess.DoesNotExist:
                pass

    def set_shipment(self):
        try:
            self.shipment = Shipment.objects.get(order=self.order)
        except Shipment.DoesNotExist:
            messages.error(self.request, "Couldn't find the shipment. Please contact with administrator.")

    def set_permission_level(self):
        if self.order.access_code and self.order.owner is None:
            self.access = self.get_access_object()
            if self.access:
                self.permission = self.TEMP_ACCESS
            else:
                self.permission = self.NO_ACCESS
        elif self.order.access_code is None and self.order.owner:
            self.permission = self.USER_AUTHENTICATED
        elif self.order.access_code is None and self.order.owner is None:
            self.permission = self.NEED_ACCESS_CODE
        else:
            self.permission = self.UNKNOWN_ERROR

    def set_access_context(self):
        self.context['user'] = self.user if self.permission == self.USER_AUTHENTICATED else None
        self.context['shipment'] = self.shipment
        self.context['order'] = self.order
        if self.order.status >= Order.PAID:
            try:
                self.context['payment'] = Payment.objects.get(order__id=self.order.id)
            except Payment.DoesNotExist:
                self.context['payment'] = True
        else:
            self.context['api_key'] = str(settings.PAYPAL_API_KEY[0]) if settings.PAYPAL_API_KEY else ''

    def set_no_access_context(self):
        self.context['access_code'] = True
        self.context['ref_code'] = self.order.ref_code
        self.context['oidb64'] = self.oidb64

    def update_order_if_temp_access(self):
        self.order.access_code = None
        fields_to_update = ['access_code']

        if self.order.status < Order.CONFIRMED:
            self.order.status = Order.CONFIRMED
            fields_to_update.append('status')

        self.order.save(update_fields=fields_to_update)

    def send_link_with_access_code(self):
        if self.order:
            sent = send_purchase_link(self.request, self.order)
            if sent:
                messages.success(self.request, "Access code has been sent to your e-mail")
            else:
                messages.error(self.request, "Problem occured during sending access code. Contact with administrator")

    def set_context_data(self, request, **kwargs):
        self.order = kwargs['order']
        self.user = request.user
        self.session = self.get_user_session()

        self.set_shipment()
        if self.shipment:
            self.set_permission_level()
            if self.permission in self.HAS_ACCESS:
                self.set_access_context()
            elif self.permission == self.NO_ACCESS:
                self.set_no_access_context()
