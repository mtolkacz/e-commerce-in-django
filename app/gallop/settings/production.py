from .base import *

DEBUG = False

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': get_env_variable('SQL_ENGINE'),
        'NAME': get_env_variable('SQL_DATABASE'),
        'USER': get_env_variable('SQL_USER'),
        'PASSWORD': get_env_variable('SQL_PASSWORD'),
        'HOST': get_env_variable('SQL_HOST'),
        'PORT': get_env_variable('SQL_PORT'),
    }
}

PAYPAL_TEST = False

