from .base import *

DEBUG = True

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

INSTALLED_APPS += (
    'debug_toolbar',
    'sslserver',  # AN SSL-ENABLED DEVELOPMENT SERVER FOR DJANGO
)

PAYPAL_TEST = True
