from django.contrib.auth import authenticate
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone, six
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from .utils import *


class Country(models.Model):
    name = models.CharField(
        max_length=30
    )

    def __str__(self):
        return '{}'.format(self.name)


class Voivodeship(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=30
    )

    def __str__(self):
        return '{}'.format(self.name)


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active)
        )


account_activation_token = TokenGenerator()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

    @staticmethod
    def create_from_form(form):
        # Save form but not commit yet
        user = form.save(commit=False)

        # Set deactivated till mail confirmation
        user.is_active = False

        # Create new user
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    first_name = models.CharField(
        _('first name'),
        max_length=50
    )
    last_name = models.CharField(
        _('last name'),
        max_length=150
    )
    email = models.EmailField(
        _('email address'),
        unique=True,
        null=True
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
    picture = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True
    )

    # phone = models.IntegerField(default=0)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    """ Billing data - required fields to complete order. """
    BILLING_DATA = [first_name, last_name, address_1, city, voivodeship, country, zip_code]

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = False

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_picture_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            return self.picture.url
        else:
            return "/media/avatar.png"

    def get_full_name(self):
        """ Return the first_name plus the last_name, with a space in between. """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """ Return the short name for the user. """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """ Send an email to this user. """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def has_all_billing_data(self):
        """ Check if user object contains all required billing data. """
        return not any(getattr(self, field.name) is None
                       or getattr(self, field.name) == '' for field in self.BILLING_DATA)

    def update_from_form(self, form):
        if form.has_changed():
            fields_to_update = form.changed_data
            for field in form.changed_data:
                setattr(self, field, form.cleaned_data[field])

            self.save(update_fields=fields_to_update)

    def activate(self):
        # Activate user and save
        self.is_active = True
        self.save()

    @staticmethod
    def get_decrypted_object(uidb64):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass

    def send_activation_link(self, request, **kwargs):
        # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
        current_site = get_current_site(request)

        # Create Email object, prepare mail content and generate user token
        # Email class includes custom predefined SMTP settings

        receiver = self.email
        subject = 'Activate your Gallop account'
        context = {
            'user': self,
            'domain': current_site.domain,
            # Return a bytestring version of user.pk and encode a bytestring to a base64 string
            # for use in URLs, stripping any trailing equal signs.
            'uid': urlsafe_base64_encode(force_bytes(self.pk)),
            'token': account_activation_token.make_token(self),  # Generate user token
        }
        if 'order' in kwargs:
            context['oid'] = urlsafe_base64_encode(force_bytes(kwargs['order'].id))  # Generate user token
            template_name = 'accounts/purchase_activate.html'
        else:
            template_name = 'accounts/activate.html'

        message = render_to_string(template_name, context)
        send_email.apply_async((receiver, subject, message), countdown=0)  # Celery sending mail

    @staticmethod
    def authenticate_from_form(form):
        login = form.cleaned_data.get('username')  # Normalize form fields to consistent format
        raw_password = form.cleaned_data.get('password')
        username = User.objects.get(email=login).username if login.find('@') >= 0 else login

        # If the given credentials are valid, return a User object.
        return authenticate(username=username, password=raw_password)

    @staticmethod
    def set_session_expiration(request):
        # Check if remember me checkbox is selected
        if not request.POST.get('remember_me', None):
            # Set a custom expiration for the session to 0.
            # The session will expire on browser close.
            request.session.set_expiry(0)
