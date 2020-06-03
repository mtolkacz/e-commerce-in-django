from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Country, Voivodeship
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column


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
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Login'}))
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    address_1 = forms.CharField(
        label='Address',
        max_length=100,
        widget=forms.TextInput()
    )
    address_2 = forms.CharField(
        required=False,
        max_length=100,
        label='Address 2',
        widget=forms.TextInput()
    )
    country = forms.ModelChoiceField(queryset=Country.objects.all())
    voivodeship = forms.ModelChoiceField(queryset=Voivodeship.objects.all())
    city = forms.CharField(max_length=50)
    zip_code = forms.CharField(max_length=6)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',
                  'first_name', 'last_name', 'address_1', 'address_2',
                  'country', 'voivodeship', 'city', 'zip_code', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'username',
            'email',
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'address_1',
            'address_2',
            Row(
                Column('voivodeship', css_class='form-group'),
                css_class='form-row'
            ),
            Row(
                Column('country', css_class='form-group col-md-4'),
                Column('city', css_class='form-group col-md-4'),
                Column('zip_code', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            Submit('register', 'Create Account', css_class="btn btn-primary btn-block")
        )


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    address_1 = forms.CharField(
        label='Address',
        max_length=100,
        widget=forms.TextInput()
    )
    address_2 = forms.CharField(
        required=False,
        max_length=100,
        label='Address 2',
        widget=forms.TextInput()
    )
    country = forms.ModelChoiceField(queryset=Country.objects.all())
    voivodeship = forms.ModelChoiceField(queryset=Voivodeship.objects.all())
    city = forms.CharField(max_length=50)
    zip_code = forms.CharField(max_length=6)
    picture = forms.FileField(label="Select a file", required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'address_1', 'address_2',
                  'country', 'voivodeship', 'city', 'zip_code', 'picture', )


