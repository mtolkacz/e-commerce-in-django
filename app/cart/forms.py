from django import forms
from accounts.models import User, Country, Voivodeship
from cart.models import Shipment,ShipmentType
from django.contrib.auth.forms import UserCreationForm


class BillingForm(UserCreationForm):
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
        fields = ('email', 'first_name', 'last_name', 'username', 'password1', 'password2',
                  'address_1', 'address_2', 'country', 'voivodeship', 'city', 'zip_code', )

    def __init__(self, *args, **kwargs):
        without_new_account = kwargs.pop('without_new_account', False)
        super(BillingForm, self).__init__(*args, **kwargs)
        if without_new_account:
            self.fields['email'].required = False
            self.fields['username'].required = False
            self.fields['password1'].required = False
            self.fields['password2'].required = False


class ShipmentForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
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
    zip_code = forms.CharField(max_length=6)

    class Meta:
        model = Shipment
        fields = ('address_1', 'address_2', 'country', 'voivodeship', 'zip_code', )


class ShipmentTypeForm(forms.Form):
    delivery = forms.ModelChoiceField(label=False, queryset=ShipmentType.objects.all())

    class Meta:
        fields = 'delivery'
