from django.contrib import admin
from .models import Product, Category, Subdepartment, Department, Brand


class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ['name',
                    'get_brand_name',
                    'description',
                    'price',
                    'get_department_name',
                    'get_subdepartment_name',
                    'get_category_name',
                    'image_tag', ]

    def get_brand_name(self, obj):
        return obj.brand.name
    get_brand_name.admin_order_field = 'brand'
    get_brand_name.short_description = 'Brand Name'

    def get_department_name(self, obj):
        return obj.department.name
    get_department_name.admin_order_field = 'department'
    get_department_name.short_description = 'Department Name'

    def get_subdepartment_name(self, obj):
        return obj.subdepartment.name
    get_subdepartment_name.admin_order_field = 'subdepartment'
    get_subdepartment_name.short_description = 'Subdepartment Name'

    def get_category_name(self, obj):
        return obj.category.name
    get_category_name.admin_order_field = 'category'
    get_category_name.short_description = 'Category Name'


class SubdepartmentAdmin(admin.ModelAdmin):
    model = Subdepartment
    list_display = ['name', 'get_department_name', ]

    def get_department_name(self, obj):
        return obj.department.name
    get_department_name.admin_order_field = 'department'
    get_department_name.short_description = 'Department Name'


class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ['name', 'get_subdepartment_name', ]

    def get_subdepartment_name(self, obj):
        return obj.subdepartment.name
    get_subdepartment_name.admin_order_field = 'subdepartment'
    get_subdepartment_name.short_description = 'Subdepartment Name'


class BrandAdmin(admin.ModelAdmin):
    model = Brand
    list_display = ['name', 'get_brand_name', ]

    def get_brand_name(self, obj):
        return obj.brand.name
    get_brand_name.admin_order_field = 'brand'
    get_brand_name.short_description = 'Brand Name'


admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Subdepartment, SubdepartmentAdmin)
admin.site.register(Department)


