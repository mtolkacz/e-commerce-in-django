# from django.forms import ModelForm
from django import forms
from accounts.models import User, Country, Voivodeship


class CheckoutForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField()
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    address_1 = forms.CharField(
        label='Address',
        widget=forms.TextInput()
    )
    address_2 = forms.CharField(
        required=False,
        label='Address 2',
        widget=forms.TextInput()
    )
    country = forms.ModelChoiceField(queryset=Country.objects.all())
    voivodeship = forms.ModelChoiceField(queryset=Voivodeship.objects.all())
    city = forms.CharField()
    zip_code = forms.CharField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email',
                  'address_1', 'address_2', 'country', 'voivodeship', 'city', 'zip_code', )


