from django.contrib import admin
from .models import Product, Category, Subdepartment, Department, \
    Brand, DiscountType, DiscountPriorityType, Discount, DiscountCustom, \
    DiscountStatus
from django.apps import apps


class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ['id',
                    'name',
                    'get_brand_name',
                    'price',
                    'get_discounted_price',
                    'get_discount_value',
                    'get_department_name',
                    'get_subdepartment_name',
                    'get_category_name',
                    'image_tag', ]

    def get_discount_value(self, obj):
        return '-{}%'.format(obj.get_discount_value()) if obj.discounted_price else ''
    get_discount_value.admin_order_field = 'discounted_price'
    get_discount_value.short_description = 'Discount value'

    def get_discounted_price(self, obj):
        return obj.discounted_price if obj.discounted_price else ''
    get_discounted_price.admin_order_field = 'discounted_price'
    get_discounted_price.short_description = 'Discounted price'

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
    list_display = ['id', 'name', 'get_department_name', 'image_tag1', 'image_tag2', ]

    def get_department_name(self, obj):
        return obj.department.name
    get_department_name.admin_order_field = 'department'
    get_department_name.short_description = 'Department Name'


class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ['id', 'name', 'get_subdepartment_name', 'image_tag1', 'image_tag2', ]  # 71FS38eUaoL._SX425_.jpg

    def get_subdepartment_name(self, obj):
        return obj.subdepartment.name
    get_subdepartment_name.admin_order_field = 'subdepartment'
    get_subdepartment_name.short_description = 'Subdepartment Name'


class BrandAdmin(admin.ModelAdmin):
    model = Brand
    list_display = ['id', 'name', 'get_brand_name', ]

    def get_brand_name(self, obj):
        return obj.name
    get_brand_name.admin_order_field = 'brand'
    get_brand_name.short_description = 'Brand Name'


class DiscountAdmin(admin.ModelAdmin):
    model = Discount
    list_display = ['id', 'name', 'get_status_name', 'get_percentage_value', 'get_type_name', 'get_set_name',
                    'get_priority_name', 'get_priority_value', 'startdate', 'enddate',
                    'description']

    def get_percentage_value(self, obj):
        return str(obj.value) + '%'

    def get_status_name(self, obj):
        return obj.status.name

    def get_type_name(self, obj):
        return obj.type.name

    def get_set_name(self, obj):
        model_name = obj.type.model
        Model = apps.get_model(app_label='products', model_name=model_name)
        set_object = Model.objects.get(id=obj.set_id)
        return set_object.name

    def get_priority_value(self, obj):
        return obj.priority.value

    def get_priority_name(self, obj):
        return obj.priority.name

    get_status_name.short_description = 'status'
    get_type_name.short_description = 'type'
    get_priority_value.short_description = 'priority value'
    get_priority_name.short_description = 'priority'
    get_set_name.short_description = 'set name'
    get_percentage_value.short_description = 'percentage discount'


class DiscountTypeAdmin(admin.ModelAdmin):
    model = DiscountType
    list_display = ['name']


class DiscountPriorityTypeAdmin(admin.ModelAdmin):
    model = DiscountType
    list_display = ['name', 'value', 'description']


class DiscountCustomAdmin(admin.ModelAdmin):
    model = DiscountCustom
    list_display = ['name', 'value', ]


class DiscountStatusAdmin(admin.ModelAdmin):
    model = DiscountStatus
    list_display = ['name', ]


admin.site.register(DiscountStatus, DiscountStatusAdmin)
admin.site.register(DiscountCustom, DiscountCustomAdmin)
admin.site.register(DiscountPriorityType, DiscountPriorityTypeAdmin)
admin.site.register(DiscountType, DiscountTypeAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Subdepartment, SubdepartmentAdmin)
admin.site.register(Department)


