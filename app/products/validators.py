from django.core.exceptions import ValidationError


def ProductIDsValidator(value):
    product_list = value.split(';')
    for i in product_list:
        if not isinstance(i, int):
            raise ValidationError("This field accepts only integer values")
    return value
