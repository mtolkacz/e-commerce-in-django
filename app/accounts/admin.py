from django.contrib import admin

from .models import Country, User, Voivodeship


class CountryAdmin(admin.ModelAdmin):
    model = Country
    list_display = ['name', ]


class VoivodeshipAdmin(admin.ModelAdmin):
    model = Voivodeship
    list_display = ['name', 'get_country_name', ]

    def get_country_name(self, obj):
        return obj.country.name
    get_country_name.short_description = 'Country'


class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = ['username', 'first_name', 'last_name', 'image_tag', 'email', 'country',
                    'voivodeship', 'address_1', 'address_2', 'zip_code', 'city', ]


admin.site.register(User, UserAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Voivodeship, VoivodeshipAdmin)
