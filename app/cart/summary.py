from django.contrib import messages
from django.contrib.sessions.models import Session
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from accounts.models import User
from .models import Order, OrderAccess, Shipment, Payment
from gallop import settings


class Summary:
    # permission level
    NO_ACCESS = 1
    TEMP_ACCESS = 2
    USER_AUTHENTICATED = 3
    NEED_ACCESS_CODE = 4
    UNKNOWN_ERROR = None
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

    def __init__(self, request, ref_code, oidb64):
        self.request = request
        self.ref_code = ref_code
        self.oidb64 = oidb64
        self.user_authenticated = request.user.is_authenticated
        self.user = self.get_user_object()
        self.session = self.get_or_create_user_session()
        self.context = {}
        self.order = None
        self.shipment = None
        self.has_access = None
        self.permission = None

    # 0.a) init
    def get_user_object(self):
        user = None
        if self.request:
            try:
                user = User.objects.get(id=self.request.user.id)
            except User.DoesNotExist:
                pass
        return user

    # 0.b) init
    def get_or_create_user_session(self):
        session = None
        if self.request:
            session = self.request.session.session_key
            if not session:
                self.request.session['guest'] = True
                self.request.session.save()
                session = self.request.session
            try:
                session = Session.objects.get(session_key=self.request.session.session_key)
            except Session.DoesNotExist:
                pass
        return session

    # 1.
    def set_order(self):
        self.order = self.get_encrypted_order()
        return self.order

    # 2.
    def set_shipment(self):
        self.shipment = self.get_shipment()
        if not self.shipment:
            messages.error("Couldn't find the shipment. Please contact with administrator.")
        return self.shipment

    # 3.
    def set_permission(self):
        self.permission = self.get_permission_level()

    # 4.
    def set_context(self):
        if self.permission:
            if self.permission == self.TEMP_ACCESS or self.permission == self.USER_AUTHENTICATED:
                self.context['user'] = self.user if self.user else self.shipment
                self.context['shipment'] = self.shipment
                self.context['order'] = self.order
                if self.order.status == Order.PAID:
                    try:
                        payment = Payment.objects.get(order__id=self.order.id)
                    except Payment.DoesNotExist:
                        payment = True
                    self.context['payment'] = payment
                else:
                    self.context['api_key'] = str(settings.PAYPAL_API_KEY[0]) if settings.PAYPAL_API_KEY else ''
            elif self.permission == self.NO_ACCESS:
                self.context['access_code'] = True
                self.context['ref_code'] = self.order.ref_code
                self.context['oidb64'] = self.oidb64

    def get_shipment(self):
        shipment = None
        if self.order:
            try:
                shipment = Shipment.objects.get(order=self.order)
            except Shipment.DoesNotExist:
                pass
        return shipment

    def get_encrypted_order(self):
        order = None
        try:
            oid = force_text(urlsafe_base64_decode(self.oidb64))
        except(TypeError, ValueError, OverflowError):
            pass
        else:
            dict = {
                'key': 'owner' if self.user_authenticated else 'owner__isnull',
                'value': self.user if self.user_authenticated else True,
            }
            try:
                order = Order.objects.get(**{dict['key']: dict['value']}, id=oid, ref_code=self.ref_code)
            except Order.DoesNotExist:
                pass
        return order

    def get_access_object(self):
        access = None
        if self.session:
            try:
                access = OrderAccess.objects.get(session_key=self.session)
            except OrderAccess.DoesNotExist:
                pass
        return access

    def send_link_with_access_code(self):
        if self.order:
            from .views import send_purchase_link
            sent = send_purchase_link(self.request, self.order)
            if sent:
                messages.success(self.request, "Access code has been sent to your e-mail")
            else:
                messages.error(self.request, "Problem occured during sending access code. Contact with administrator")

    def get_permission_level(self):
        if self.order:
            if self.order.access_code and self.order.owner is None:
                self.has_access = self.get_access_object()
                if self.has_access:
                    return self.TEMP_ACCESS
                else:
                    return self.NO_ACCESS
            elif self.order.access_code is None and self.order.owner:
                return self.USER_AUTHENTICATED
            elif self.order.access_code is None and self.order.owner is None:
                return self.NEED_ACCESS_CODE
        return self.UNKNOWN_ERROR