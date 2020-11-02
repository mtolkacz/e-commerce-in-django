from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic.base import View

from products.models import Favorites, Product, ProductRating
from accounts.forms import LoginForm, RegisterForm, ProfileForm
from accounts.models.User import authenticate_from_form
from accounts.models.UserManager import create_from_form
from cart.models import Order
from accounts.models import User, account_activation_token


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

        if 'login' in request.POST:  # Check if login button is clicked
            login_form = LoginForm(request.POST)  # Assign login form fields to variable

            if login_form.is_valid():  # Return True if the form has no errors, or False otherwise
                try:
                    user = authenticate_from_form(login_form)
                except User.DoesNotExist:
                    messages.error(request, 'Incorrect login')

                if not user:  # Check if credentials are valid and User object exist
                    messages.error(request, 'Invalid login details given.')
                else:
                    if not user.is_active:  # Report error if user is not active
                        messages.error(request, 'Your account is inactive.')
                    else:
                        auth_login(request, user)  # Log in user
                        user.set_session_expiration(request)
                        next_url = request.GET.get('next')
                        if next_url:
                            return HttpResponseRedirect(next_url)

                        hello = user.first_name if user.first_name else user.username
                        messages.success(request, 'Welcome {}'.format(hello))
                        return redirect(self.page_to_redirect)  # Go to index view

        elif 'register' in request.POST:

            registration_form = RegisterForm(request.POST)  # Assign register form fields to variable

            if registration_form.is_valid():  # Return True if the form has no errors, or False otherwise
                user = create_from_form(registration_form)
                user.send_activation_link(request)
                messages.success(request, 'Please confirm your email address to complete the registration.')
            else:
                ctxt['registration_form'] = registration_form

        return render(request, self.template_name, self.get_context_data(**ctxt))


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    @staticmethod
    def get_context_data(request, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = ProfileForm(instance=request.user)

        orders = Order.objects.filter(owner=request.user)
        favorites = Favorites.objects.filter(user=request.user)

        # todo how rewrite below especially queries
        product_ids = []
        for order in orders:
            if order.status == Order.COMPLETED:
                # get list of products in orders
                product_ids += order.items.all().values_list('product__id', flat=True)

        product_ids = list(set(product_ids))
        rated_products = ProductRating.objects\
            .filter(product__in=product_ids, user=request.user).defer('user')

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
    if user and account_activation_token.check_token(user, token):
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
