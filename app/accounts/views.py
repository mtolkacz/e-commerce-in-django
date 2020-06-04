from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegisterForm
from . import functions as act
from .tokens import account_activation_token
from .models import User
from accounts.forms import ProfileForm
from cart.models import Order
from gallop import functions as glp
from products.models import Product, Favorites


@require_http_methods(["GET", "POST"])
def login(request):

    # If user is already singed in redirect to index view
    if request.user.is_authenticated:
        return redirect('index')

    # Create multiple forms for signing in and registration
    login_form = LoginForm()
    registration_form = RegisterForm()

    # Go to login and register logic section if method is POST
    if request.method == 'POST':

        # Check if login button is clicked
        if 'login' in request.POST:
            # Assign login form fields to variable
            login_form = LoginForm(request.POST)

            # Return True if the form has no errors, or False otherwise
            if login_form.is_valid():

                # Normalize form fields to consistent format
                login = login_form.cleaned_data.get('username')
                raw_password = login_form.cleaned_data.get('password')

                username = login
                if username.find('@') >= 0:
                    try:
                        username = User.objects.get(email=login).username
                    except User.DoesNotExist:
                        messages.error(request, 'Incorrect login')

                # If the given credentials are valid, return a User object.
                user = authenticate(username=username, password=raw_password)

                # Check if credentials are valid and User object exist
                if user is not None:

                    # Check if user is active
                    if user.is_active:

                        # Log in user
                        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                        # Check if remember me checkbox is selected
                        if not request.POST.get('remember_me', None):
                            # Set a custom expiration for the session to 0.
                            # The session will expire on browser close.
                            request.session.set_expiry(0)

                        next_url = request.GET.get('next')
                        if next_url:
                            return HttpResponseRedirect(next_url)

                        hello = user.first_name if user.first_name else user.username
                        messages.success(request, 'Welcome {}'.format(hello))
                        # Go to index view
                        return redirect('index')
                    else:
                        messages.error(request, 'Your account is inactive.')
                else:
                    messages.error(request, 'Invalid login details given.')

        # Check if register button is clicked
        elif 'register' in request.POST:

            # Assign register form fields to variable
            registration_form = RegisterForm(request.POST)

            # Return True if the form has no errors, or False otherwise
            if registration_form.is_valid():

                user = glp.create_user_from_form(registration_form)

                act.send_activation_link(request, user)

    # Load login view with forms and display form messages
    return render(request, 'accounts/login.html',
                  {'login_form': login_form,
                   'registration_form': registration_form})


# Logout and load logout information or redirect to index view if user is not signed in
def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect('index')


def update_obj_from_form(obj, form):
    fields_to_update = []
    for form_field in form.fields:
        try:
            obj_field = obj._meta.get_field(form_field)
        except FieldDoesNotExist:
            obj_field = None
        if obj_field:
            if obj_field.many_to_one:
                new_model = getattr(obj, form_field)._meta.model
                new_object = new_model.objects.get(id=obj_field.value_from_object(obj))
                obj_field_value = str(new_object)
            else:
                obj_field_value = obj_field.value_from_object(obj)
                obj_field_value = None if obj_field_value == "" else obj_field_value
            cleaned = str(form.cleaned_data[form_field]) if form.cleaned_data[form_field] else None
            if obj_field_value != cleaned:
                setattr(obj, form_field, form.cleaned_data[form_field])
                fields_to_update.append(form_field)
    if fields_to_update:
        obj.save(update_fields=fields_to_update)
        return True
    else:
        return False


@login_required
def profile(request):
    user = glp.get_user_object(request)
    print(f'DJANGOTEST: test')
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            print(f'DJANGOTEST: fgfgfg')
            messages.success(request, 'Data saved') if form.save() else None
            return HttpResponseRedirect(request.path)
        else:
            print(f'DJANGOTEST: ff')
    else:
        form = ProfileForm(instance=user)

    context = {
        'form': form,
        'favorites': Favorites.objects.filter(user=user),
        'orders': Order.objects.filter(owner=user)
    }
    return render(request, 'accounts/profile.html', context)


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
