# from django.forms import ModelForm
from django import forms
from .models import Order, OrderItem


class OrderForm(forms.ModelForm):
    amount = forms.CharField(label='')

    class Meta:
        model = OrderItem
        fields = ('amount', )

