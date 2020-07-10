from django import forms

from .models import Product, Category


class ProductForm(forms.ModelForm):
    category_name = forms.ModelChoiceField(queryset=Category.objects.all(),
                                           to_field_name='name',
                                           empty_label='Select category')

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category_name', 'thumbnail']
