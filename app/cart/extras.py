import string
import random
from datetime import date
import datetime
from .models import OrderItem


def save_order_item(order):
    order_item = OrderItem.objects.get_or_create(order=order)
    order_item.save()
    return order_item


def generate_order_id():
    date_str = date.today().strftime('%Y%m%d')[2:] + str(datetime.datetime.now().second)
    rand_str = "".join([random.choice(string.digits) for count in range(3)])
    return date_str + rand_str
