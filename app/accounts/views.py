from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from .forms import LoginForm, RegisterForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from .tokens import account_activation_token
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from .models import User
from .tasks import send_email


def create_user_from_form(form):
    # Save form but not commit yet
    user = form.save(commit=False)

    # Set deactivated till mail confirmation
    user.is_active = False

    # Create new user
    user.save()

    return user


def send_activation_link(request, user, **kwargs):

    # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
    current_site = get_current_site(request)

    # # Create Email object, prepare mail content and generate user token
    # # Email class includes custom predefined SMTP settings

    print('DJANGOTEST: Username = {}, mail = {}'.format(user.username, user.email))
    # receiver = form.cleaned_data.get('email')
    receiver = user.email
    subject = 'Activate your Gallop account'
    if 'order' in kwargs:
        context = {
            'user': user,
            'domain': current_site.domain,
            # Return a bytestring version of user.pk and encode a bytestring to a base64 string
            # for use in URLs, stripping any trailing equal signs.
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            # Generate user token
            'token': account_activation_token.make_token(user),
            # Generate user token
            'oid': urlsafe_base64_encode(force_bytes(kwargs['order'].id)),
        }
        print('DJANGOTEST: kwargs = {}'.format(kwargs['order'].id))
        message = render_to_string('accounts/purchase_activate.html', context)
    else:
        context = {
            'user': user,
            'domain': current_site.domain,
            # Return a bytestring version of user.pk and encode a bytestring to a base64 string
            # for use in URLs, stripping any trailing equal signs.
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            # Generate user token
            'token': account_activation_token.make_token(user)
        }
        message = render_to_string('accounts/activate.html', context)

    # Celery sending mail
    send_email.apply_async((receiver, subject, message), countdown=0)
    messages.success(request, 'Please confirm your email address to complete the registration.')


# Multiple view for signing in and registration
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

                user = create_user_from_form(registration_form)

                send_activation_link(request, user)

    # Load login view with forms and display form messages
    return render(request, 'accounts/login.html',
                  {'login_form': login_form,
                   'registration_form': registration_form})


# Logout and load logout information or redirect to index view if user is not signed in
def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect('index')


def profile(request):
    if request.user.is_authenticated:
        return render(request, 'accounts/profile.html')
    else:
        return redirect('login')


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
