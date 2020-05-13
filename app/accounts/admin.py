from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Country, Voivodeship


class CountryAdmin(admin.ModelAdmin):
    model = Country
    list_display = ['name', ]


class VoivodeshipAdmin(admin.ModelAdmin):
    model = Voivodeship
    list_display = ['name', 'get_country_name', ]

    def get_country_name(self, obj):
        return obj.country.name
    get_country_name.short_description = 'Country'


admin.site.register(User, UserAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Voivodeship, VoivodeshipAdmin)
