import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models import signals
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from accounts.models import Country, Voivodeship
from accounts.utils import validate_zip_code
from products.models import Product
from .signals import order_pre_delete, shipment_pre_save

User = get_user_model()
MAX_ITEMS_IN_CART = 30


class PromoCode(models.Model):
    PERCENTAGE = 1
    VALUE = 2
    TYPE = (
        (PERCENTAGE, 'Percentage cart discount'),
        (VALUE, 'Value cart discount'),
    )
    code = models.CharField(
        max_length=15
    )
    type = models.PositiveSmallIntegerField(
        choices=TYPE,
        default=PERCENTAGE,
    )
    value = models.PositiveSmallIntegerField()
    minimum_order_value = models.PositiveSmallIntegerField(
        null=True
    )
    active = models.BooleanField(
        default=False
    )

    def __str__(self):
        return '{}'.format(self.code)


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True
    )
    date_added = models.DateTimeField(
        auto_now=True
    )
    date_ordered = models.DateTimeField(
        null=True
    )
    amount = models.IntegerField(
        default=1
    )
    price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='USD',
        null=True
    )
    booked = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.product.name

    def is_discounted(self):
        return True if self.product.discounted_price else False

    def get_item_total_no_discount(self):
        return self.product.price * self.amount

    def get_item_total(self):
        return (self.product.discounted_price if self.product.discounted_price else self.product.price) * self.amount


class Order(models.Model):
    IN_CART = 1
    BOOKED = 2
    CONFIRMED = 3
    PAID = 4
    COMPLETED = 5
    STATUS = (
        (IN_CART, 'Products in cart - not booked yet'),
        (BOOKED, 'Stock booked'),
        (CONFIRMED, 'Confirmed by client'),
        (PAID, 'Paid - waiting for delivery'),
        (COMPLETED, 'Completed - Delivered to client'),
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True
    )
    ref_code = models.CharField(
        max_length=20,
        editable=False
    )
    is_ordered = models.BooleanField(
        default=False
    )
    items = models.ManyToManyField(OrderItem)
    date_ordered = models.DateTimeField(
        default=timezone.now
    )
    session_key = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        null=True,
        editable=False
    )
    access_code = models.SmallIntegerField(
        null=True,
        editable=False
    )
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        editable=False
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUS,
        default=IN_CART,
    )
    # save email for client without account which don't want to create one
    email = models.EmailField(
        null=True
    )

    def get_summary_url(self):
        return reverse('summary', kwargs={'ref_code': self.ref_code,
                                          'oidb64': urlsafe_base64_encode(force_bytes(self.id)), })

    def delete(self):
        items = self.items.all()
        for item in items:
            if self.status == self.BOOKED:
                if item.booked:
                    item.product.undo_book()
            item.delete()
        return super(Order, self).delete()

    def get_cart_items(self):
        return self.items.all().order_by('id')

    def get_shipment_cost(self):
        try:
            shipment_type = Shipment.objects.get(order=self)
        except Shipment.DoesNotExist:
            shipment_type = None
        return shipment_type.cost if shipment_type else 0

    def get_promo_code_value(self):
        cart_total = sum([(item.product.discounted_price if item.product.discounted_price else item.product.price)
                          * item.amount for item in self.items.all()])
        promo_value = 0
        if self.promo_code:
            if self.promo_code.type == PromoCode.VALUE:
                promo_value = Decimal(self.promo_code.value)
            elif self.promo_code.type == PromoCode.PERCENTAGE:
                promo_value = Decimal(cart_total.amount) - Decimal(cart_total.amount * Decimal((100 - self.promo_code.value) / 100))
        promo = Money(promo_value, str(cart_total.currency))
        return promo

    def get_cart_total(self):
        cart_total = sum([(item.product.discounted_price if item.product.discounted_price else item.product.price)
                          * item.amount for item in self.items.all()])

        cart_total = round(cart_total - self.get_promo_code_value() + self.get_shipment_cost(), 2)

        return cart_total

    def get_cart_total_str(self):
        return str(self.get_cart_total().amount)

    def get_cart_total_no_promo(self):
        cart_total = sum([(item.product.discounted_price if item.product.discounted_price else item.product.price)
                          * item.amount for item in self.items.all()])
        return cart_total

    def get_cart_total_no_promo_str(self):
        return str(self.get_cart_total_no_promo().amount)

    def get_cart_currency(self):
        return self.get_cart_total().currency if self.get_cart_total().currency else 'USD'

    def get_cart_qty(self):
        return sum(item.amount for item in self.items.all())

    def book(self):
        items = self.items.all()
        for item in items:
            item.product.book(amount=item.amount)
            item.booked = True
            item.save(update_fields=['booked'])
        self.update_status(self.BOOKED)

    def __str__(self):
        return '{}'.format(self.ref_code)

    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status', ])

    def create_access_code(self):
        self.access_code = random.randint(1000, 9999)
        self.save(update_fields=['access_code'])

    def delete_access_code(self):
        self.access_code = None
        self.save(update_fields=['access_code'])

    def apply_promo_code(self, promo_code):
        self.promo_code = promo_code
        self.save(update_fields=['promo_code'])


signals.pre_delete.connect(order_pre_delete, sender=Order)


class PromoCodeUsage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE
    )
    promocode = models.ForeignKey(
        PromoCode,
        on_delete=models.CASCADE
    )


class ShipmentType(models.Model):
    name = models.CharField(
        max_length=50
    )
    cost = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='USD'
    )

    def __str__(self):
        return f'{self.name} - {self.cost}'


class Shipment(models.Model):
    NEW = 1
    IN_PREPARATION = 2
    SENT = 3
    DELIVERED = 4
    STATUS = (
        (NEW, 'New and before payment'),
        (IN_PREPARATION, 'Paid and during preparation'),
        (SENT, 'Sent to client'),
        (DELIVERED, 'Delivered to client'),
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        null=True,
        editable=False
    )
    type = models.ForeignKey(
        ShipmentType,
        on_delete=models.CASCADE,
        null=True
    )
    cost = MoneyField(
        null=True,
        max_digits=14,
        decimal_places=2,
        default_currency='USD'
    )
    email = models.EmailField(
        null=True
    )
    first_name = models.CharField(
        max_length=50
    )
    last_name = models.CharField(
        max_length=150
    )
    city = models.CharField(
        max_length=50
    )
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.SET_NULL,
        null=True
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True
    )
    zip_code = models.CharField(
        max_length=6,
        validators=[validate_zip_code]
    )
    address_1 = models.CharField(
        max_length=100
    )
    address_2 = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUS,
        default=NEW,
    )
    creationdate = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )
    preparationdate = models.DateTimeField(
        null=True,
        editable=False
    )
    sentdate = models.DateTimeField(
        null=True,
        editable=False
    )
    delivereddate = models.DateTimeField(
        null=True,
        editable=False
    )

    def save(self, *args, **kwargs):
        if self.type is None:
            try:
                self.type = ShipmentType.objects.get(name='DHL')
            except ShipmentType.DoesNotExist:
                self.type = ShipmentType.objects.first()

        if self.cost is None:
            self.cost = self.type.cost

        if self.email is None:
            self.email = kwargs['email'] if 'email' in kwargs else None

        if self.order is None:
            self.order = kwargs['order'] if 'order' in kwargs else None

        if self.order:
            return False  # todo add exception

        now = timezone.now()
        if self.status == self.IN_PREPARATION:
            self.preparationdate = now
        elif self.status == self.SENT:
            self.sentdate == now
        elif self.status == self.DELIVERED:
            self.delivereddate == now

        super().save(*args, **kwargs)

    def __str__(self):
        return '{} - {}'.format(self.order.ref_code, self.get_status_display())

    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status', ])


signals.pre_save.connect(shipment_pre_save, sender=Shipment)


class OrderAccess(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True
    )
    session_key = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        null=True,
        editable=False
    )


class Payment(models.Model):
    id = models.CharField(
        max_length=17,
        editable=False,
        primary_key=True
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        editable=False
    )
    createdate = models.DateTimeField(
        null=True,
        editable=False
    )
    updatedate = models.DateTimeField(
        null=True,
        editable=False
    )
    status = models.CharField(
        max_length=10,
        editable=False
    )
    value = MoneyField(
        null=True,
        max_digits=14,
        decimal_places=2,
        default_currency='USD'
    )
    payer_id = models.CharField(
        max_length=15,
        editable=False
    )
    email = models.EmailField(
        editable=False
    )
    given_name = models.CharField(
        max_length=30,
        editable=False
    )
    surname = models.CharField(
        max_length=30,
        editable=False
    )
