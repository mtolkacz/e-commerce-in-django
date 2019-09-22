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
from django.contrib.auth.models import User
from .emailct import Email


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
                username = login_form.cleaned_data.get('username')
                raw_password = login_form.cleaned_data.get('password')

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
                        # Go to index view
                        return redirect('index')
                    else:
                        messages.error(request, 'Your account was inactive.')
                else:
                    messages.error(request, 'Invalid login details given.')

        # Check if register button is clicked
        elif 'register' in request.POST:

            # Assign register form fields to variable
            registration_form = RegisterForm(request.POST)

            # Return True if the form has no errors, or False otherwise
            if registration_form.is_valid():
                # Save form but not commit yet
                user = registration_form.save(commit=False)

                # Set deactivated till mail confirmation
                user.is_active = False

                # Create new user
                user.save()

                # Look up the current site based on request.get_host() if the SITE_ID setting is not defined
                current_site = get_current_site(request)

                # Create Email object, prepare mail content and generate user token
                # Email class includes custom predefined SMTP settings
                registration_email = Email()
                receiver = registration_form.cleaned_data.get('email')
                subject = 'Activate your Come Together account'
                message = render_to_string('activate.html', {
                    'user': user,
                    'domain': current_site.domain,
                    # Return a bytestring version of user.pk and encode a bytestring to a base64 string for use in
                    # URLs, stripping any trailing equal signs.
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    # Generate user token
                    'token': account_activation_token.make_token(user)
                })

                # Send e-mail with activation link through SSL
                registration_email.send(receiver, subject, message)

                # Add feedback message to user to check mailbox
                messages.success(request, 'Please confirm your email address to complete the registration.')

    # Load login view with forms and display form messages
    return render(request, 'login.html',
                  {'login_form': login_form,
                   'registration_form': registration_form})


# Logout and load logout information or redirect to index view if user is not signed in
def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
        return render(request, 'logout.html')
    else:
        return redirect('index')


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
        return render(request, 'successful_register.html')
    else:
        return redirect('index')
