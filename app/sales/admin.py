from django.contrib import admin

from .models import Sale


class SaleAdmin(admin.ModelAdmin):
    model = Sale
    list_display = ['id', 'get_product_name', 'date', 'price', 'get_promo_code_name', ]

    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = 'Product'

    def get_promo_code_name(self, obj):
        return obj.promo_code.code if obj.promo_code else '-'
    get_promo_code_name.short_description = 'Promo code'


admin.site.register(Sale, SaleAdmin)
