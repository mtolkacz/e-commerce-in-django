import os
import socket
from django.core.exceptions import ImproperlyConfigured

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + '1' for ip in ips] + ['127.0.0.1', '10.0.2.2']

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/


def get_env_variable(var_name):
    """Get the environment variable or return exception. Code from Two scoops of Django."""
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the {} environment variable".format(var_name)
        raise ImproperlyConfigured(error_msg)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable('SECRET_KEY')

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_URL = 'logout'
LOGOUT_REDIRECT_URL = 'index'

# HTTPS and cookies
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True  # The SecurityMiddleware redirects all non-HTTPS requests to HTTPS
SESSION_COOKIE_SECURE = True  # Cookies will only be sent via HTTPS connection
SESSION_COOKIE_AGE = 3600  # The age of session cookies, in seconds. Set to 1 hour.
CSRF_COOKIE_SECURE = True  # CSRF cookies will only be sent via HTTPS connection
SECURE_HSTS_SECONDS = 3600

# Expire date of session cookie will be extended after every request
# Save session after every request
SESSION_SAVE_EVERY_REQUEST = True

# Twitter social auth
SOCIAL_AUTH_TWITTER_KEY = get_env_variable('SOCIAL_AUTH_TWITTER_KEY')
SOCIAL_AUTH_TWITTER_SECRET = get_env_variable('SOCIAL_AUTH_TWITTER_SECRET')

# Facebook social auth
SOCIAL_AUTH_FACEBOOK_KEY = get_env_variable('SOCIAL_AUTH_FACEBOOK_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = get_env_variable('SOCIAL_AUTH_FACEBOOK_SECRET')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'user_link']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, email, picture.type(large), link'
}
SOCIAL_AUTH_POSTGRES_JSONFIELD = True
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = [  # add this
    ('name', 'name'),
    ('email', 'email'),
    ('picture', 'picture'),
    ('link', 'profile_url'),
]

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_FACEBOOK_FIELD_SELECTORS = ['email', ]

# Celery configuration
CELERY_BROKER_URL = 'amqp://rabbitmq'
CELERY_RESULT_BACKEND = 'redis://redis'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_IGNORE_RESULT = False
CELERYD_TASK_SOFT_TIME_LIMIT = 60
CELERY_TIMEZONE = 'Europe/Warsaw'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)
THIRD_PARTY_APPS = (
    'social_django',  # SOCIAL MEDIA USER AUTHENTIFICATION
    'djmoney',  # PRODUCT PRICE MONEY FIELD IN MODEL
    'crispy_forms',  # HANDLING BOOTSTRAP4 IN DJANGO FORMS
    'ckeditor',  # HTML EDITOR FOR TEXT FIELDS (e.g. product's description)
    'rest_framework',  # REST API FRAMEWORK FOR DJANGO
    'django_elasticsearch_dsl',
    'django_elasticsearch_dsl_drf',
    'django_filters',  # REST API FILTER BACKEND
    'celery',
    'django_celery_results',
    'django_celery_beat',
    'debug_toolbar',
)
LOCAL_APPS = (
    'cart',
    'products',
    'accounts',
    'blog',
    'articles',
    'comments',
    'sales',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'gallop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(os.path.join(BASE_DIR, 'templates')), 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'cart.context_processors.cart_context_processor',
            ],
        },
    },
]

# Added Twitter and Facebook
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.facebook.FacebookOAuth2',
)

WSGI_APPLICATION = 'gallop.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

# Custom static files for every apps at the project level
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static/'),
)
os.path.join('static'),

STATIC_URL = '/static/'
STATIC_ROOT = '/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'elasticsearch:9200'
    },
}

# E-mail configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_env_variable('EMAIL_HOST')
EMAIL_HOST_USER = get_env_variable('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_HOST_PASSWORD')
EMAIL_PORT = get_env_variable('EMAIL_PORT')
EMAIL_USE_TLS = True

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 2,
    'EXCEPTION_HANDLER': 'gallop.views.handler404',
}

# SANDBOX API CREDENTIALS
PAYPAL_RECEIVER_EMAIL = get_env_variable('PAYPAL_RECEIVER_EMAIL')
PAYPAL_API_KEY = get_env_variable('PAYPAL_API_KEY')
PAYPAL_SECRET = get_env_variable('PAYPAL_SECRET')

