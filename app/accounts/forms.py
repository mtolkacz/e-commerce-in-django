from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email or Login'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '******'}))
    fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_method = 'post'
        self.helper.add_input(
            Submit('login', 'Login', css_class="btn btn-primary btn-block"))


class RegisterForm(UserCreationForm):
    # username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Login'}))
    # email = forms.EmailField(max_length=200,
    #                          help_text='Required',
    #                          widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    # password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '******'}))
    # password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '******'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Login'}),
            'email': forms.TextInput(attrs={'placeholder': 'Email'}),
            'password1': forms.PasswordInput(attrs={'placeholder': '*****'}),
            'password2': forms.PasswordInput(attrs={'placeholder': '*****'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_method = 'post'
        self.helper.add_input(
            Submit('register', 'Create Account', css_class="btn btn-primary btn-block"))
