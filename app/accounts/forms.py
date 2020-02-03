from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Layout, BaseInput, Submit, Button, Div, HTML

# User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email or Login'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '******'}))
    fields = ['username', 'password']

"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_method = 'post'
        self.helper.add_input(
            Submit('login', 'Login', css_class="btn btn-primary btn-block"))
"""


class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=200,
                             help_text='Required',
                             widget=forms.TextInput(attrs={'placeholder': 'Email'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Login'}),
            'email': forms.TextInput(attrs={'placeholder': 'Email'})
        }


"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_method = 'post'
        self.helper.add_input(
            Submit('register', 'Create Account', css_class="btn btn-primary btn-block"))

    def __3init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-user\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    BaseInput('username', 'Login', css_class='form-control'),
                    css_class="input-group"),
                css_class="form-group"
            ),
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-envelope\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    css_class="input-group"),
                HTML("<br>"),
                HTML("<p class=\"text-center\">"
                     "<input type=\"checkbox\" class=\"checkbox\" name=\"remember_me\">"
                     "Keep me signed in"
                     "</p>"),
                css_class="form-group"
            ),
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-lock\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    css_class="input-group"),
                css_class="form-group"
            ),
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-lock\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    css_class="input-group"),
                css_class="form-group"
            ),
            Div(
                Button('register',
                       'Create account',
                       css_class="btn btn-primary btn-block"),
                css_class="form-group"
            ),
            HTML("<p class=\"text-center\">"
                 "<a href=\"\">Forgot password?</a>"
                 "</p>"),
        )
        self.helper.form_method = 'post'
        # self.helper.add_input( )

    def __3init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-user\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    BaseInput('username', 'Login', css_class='form-control'),
                    css_class="input-group"),
                css_class="form-group"
            ),
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-envelope\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    Column('email', 'Email', css_class='form-control'),
                    css_class="input-group"),
                HTML("<br>"),
                HTML("<p class=\"text-center\">"
                     "<input type=\"checkbox\" class=\"checkbox\" name=\"remember_me\">"
                     "Keep me signed in"
                     "</p>"),
                css_class="form-group"
            ),
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-lock\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    Column('password1', '*****', css_class='form-control'),
                    css_class="input-group"),
                css_class="form-group"
            ),
            Div(
                Div(
                    Div(
                        HTML("<span class=\"input-group-text\"> "
                             "<i class=\"fa fa-lock\"></i> "
                             "</span>"),
                        css_class="input-group-prepend"
                    ),
                    Column('password2', '*****', css_class='form-control'),
                    css_class="input-group"),
                css_class="form-group"
            ),
            Div(
                Button('register',
                       'Create account',
                       css_class="btn btn-primary btn-block"),
                css_class="form-group"
            ),
            HTML("<p class=\"text-center\">"
                 "<a href=\"\">Forgot password?</a>"
                 "</p>"),
        )
        self.helper.form_method = 'post'
        # self.helper.add_input( )

"""