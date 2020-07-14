from django.core.exceptions import ValidationError


def validate_product_ids(value):
    product_list = value.split(';')
    for i in product_list:
        if not isinstance(int(i), int):
            raise ValidationError("This field accepts only integer values.")
    return value
