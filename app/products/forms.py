from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    name = forms.CharField(max_length=100, widget=forms.TextInput())
    description = forms.CharField(max_length=300, widget=forms.TextInput())
    price = forms.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        model = Product
        fields = ['name', 'description', 'price']
