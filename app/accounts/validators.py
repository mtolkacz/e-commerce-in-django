import re

from django.core.exceptions import ValidationError


def ZipCodeValidator(zip_code):
    result = re.match('^\d\d-\d\d\d$', zip_code)
    if result:
        return result
    else:
        raise ValidationError("Incorrect zip code. Please input value with XX-XXX format.")
