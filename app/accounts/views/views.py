from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic.base import View

from products.models import Favorites, Product, ProductRating
from accounts.forms import LoginForm, RegisterForm, ProfileForm
from accounts.models import User
from accounts.utils import create_user_from_form, send_activation_link, account_activation_token
from cart.models import Order


class LoginRegistrationView(View):
    """ User login and registration view"""

    template_name = 'accounts/login.html'

    # Redirect the logged in user to the following page
    page_to_redirect = 'index'

    @staticmethod
    def get_context_data(**kwargs):
        if 'login' not in kwargs:
            kwargs['login_form'] = LoginForm()
        if 'register' not in kwargs:
            kwargs['registration_form'] = RegisterForm()
        return kwargs

    def get(self, request, *args, **kwargs):
        # If user is already singed in then redirect to index view
        if request.user.is_authenticated:
            return redirect(self.page_to_redirect)

        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        ctxt = {}

        # Check if login button is clicked
        if 'login' in request.POST:
            # Assign login form fields to variable
            login_form = LoginForm(request.POST)

            # Return True if the form has no errors, or False otherwise
            if login_form.is_valid():
                user = self.authenticate_from_form(request, login_form)

                # Check if credentials are valid and User object exist
                if not user:
                    messages.error(request, 'Invalid login details given.')
                else:
                    # Report error if user is not active
                    if not user.is_active:
                        messages.error(request, 'Your account is inactive.')
                    else:
                        # Log in user
                        auth_login(request, user)
                        self.set_session_expiration(request)

                        next_url = request.GET.get('next')
                        if next_url:
                            return HttpResponseRedirect(next_url)

                        hello = user.first_name if user.first_name else user.username
                        messages.success(request, 'Welcome {}'.format(hello))
                        # Go to index view
                        return redirect(self.page_to_redirect)

        elif 'register' in request.POST:

            # Assign register form fields to variable
            registration_form = RegisterForm(request.POST)

            # Return True if the form has no errors, or False otherwise
            if registration_form.is_valid():
                user = create_user_from_form(registration_form)
                send_activation_link(request, user)
            else:
                ctxt['registration_form'] = registration_form

        return render(request, self.template_name, self.get_context_data(**ctxt))

    @staticmethod
    def authenticate_from_form(request, form):
        # Normalize form fields to consistent format
        login = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password')

        username = login
        if username.find('@') >= 0:
            try:
                username = User.objects.get(email=login).username
            except User.DoesNotExist:
                messages.error(request, 'Incorrect login')

        # If the given credentials are valid, return a User object.
        return authenticate(username=username, password=raw_password)

    @staticmethod
    def set_session_expiration(request):
        # Check if remember me checkbox is selected
        if not request.POST.get('remember_me', None):
            # Set a custom expiration for the session to 0.
            # The session will expire on browser close.
            request.session.set_expiry(0)


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    @staticmethod
    def get_context_data(request, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = ProfileForm(instance=request.user)

        orders = Order.objects.filter(owner=request.user)
        favorites = Favorites.objects.filter(user=request.user)
        # todo to rewrite below especially queries
        product_ids = []
        for order in orders:
            if order.status == Order.COMPLETED:
                product_ids += order.items.all().values_list('product__id', flat=True)

        product_ids = list(set(product_ids))
        rated_products = ProductRating.objects \
            .filter(product__in=product_ids, user=request.user)

        products_to_rate = Product.objects \
            .exclude(id__in=[rating.product.id for rating in rated_products]) \
            .filter(id__in=product_ids)

        context = {
            'orders': orders,
            'favorites': favorites,
            'rated_products': rated_products,
            'products_to_rate': products_to_rate,
        }
        kwargs = {**kwargs, **context}

        return kwargs

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        ctxt = {}

        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            if form.save():
                messages.success(request, 'Data saved')
            return HttpResponseRedirect(request.path)
        else:
            ctxt['form'] = form

        return render(request, self.template_name, self.get_context_data(request, **ctxt))


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        # Activate user and save
        user.is_active = True
        user.save()

        # Log in user
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Set registered session variable to display successful_registration view
        request.session['registered'] = True
        hello = user.first_name if user.first_name else user.username
        messages.success(request, 'Welcome {}'.format(hello))

        # Load successful registration view
        return redirect('successful_registration')
    else:
        messages.error(request, 'Invalid activation link!')
        return redirect('login')


# Display success registration information if the user's registered, or redirect to index view otherwise
def successful_registration(request):
    registered = request.session.get('registered')
    if registered:
        del request.session['registered']
        return render(request, 'accounts/successful_register.html')
    else:
        return redirect('index')
