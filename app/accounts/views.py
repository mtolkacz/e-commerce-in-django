from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods


# Multiple view for signing in and registration
@require_http_methods(["GET", "POST"])
def login(request):

    # If user is already singed in redirect to index view
    if request.user.is_authenticated:
        return redirect('index')

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
                        auth_login(request, user)

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
            registration_form = UserCreationForm(request.POST)

            # Return True if the form has no errors, or False otherwise
            if registration_form.is_valid():

                # Create new user
                registration_form.save()

                # Assign session variable - used in successful_registration view
                request.session['registered'] = True

                # Load successful registration view
                return redirect('successful_registration')

    # Create multiple forms for signing in and registration if method is GET
    elif request.method == 'GET':
        login_form = LoginForm()
        registration_form = UserCreationForm()

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


# Display success registration information if the user's registered, or redirect to index view otherwise
def successful_registration(request):
    registered = request.session.get('registered')
    if registered:
        del request.session['registered']
        return render(request, 'successful_register.html')
    else:
        return redirect('index')


