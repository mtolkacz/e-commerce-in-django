from django.shortcuts import render, redirect
from .forms import LoginForm, RegistrationForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods


def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
        return render(request, 'logout.html')
    return redirect('index')


@require_http_methods(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return redirect('index')
    registered = False
    login_form = LoginForm()
    registration_form = RegistrationForm()
    if request.method == 'POST':
        if 'login' in request.POST:
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data.get('username')
                raw_password = login_form.cleaned_data.get('password')
                user = authenticate(username=username, password=raw_password)
                if user is not None:
                    if user.is_active:
                        auth_login(request, user)
                        if not request.POST.get('remember_me', None):
                            request.session.set_expiry(0)
                        return redirect('index')
                    else:
                        messages.error(request, 'Your account was inactive.')
                        return redirect('login')
                else:
                    messages.error(request, 'Invalid login details given.')
                    return redirect('login')
        elif 'register' in request.POST:
            registration_form = RegistrationForm(request.POST)
            registration_form.compare_passwords()
            if registration_form.is_valid():
                user = registration_form.save()
                user.set_password(user.password)
                user.save()
                registered = True
            else:
                print(registration_form.errors)
        else:
            messages.error(request, 'Contact with site administrator.')
            return redirect('login')
    else:
        login_form = LoginForm()
        registration_form = RegistrationForm()
    return render(request, 'login.html',
                  {'login_form': login_form,
                   'registration_form': registration_form,
                   'registered': registered})
