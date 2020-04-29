from django.utils import timezone


class DiscountManager:
    queryset = None
    discount = None
    now = None
    lookup_field = None

    def __init__(self):
        pass

    def check_if_can_be_calculated(self):
        return self.discount.startdate < self.now

    def get_current_product_discount(self, product):
        from .models import Discount, DiscountLine
        try:
            product_discount = DiscountLine.objects.exclude(discount=self.discount).filter(product=product).order_by(
                'discount__priority').first()
            current_discount = Discount.objects.get(id=product_discount.discount.id)
        except Discount.DoesNotExist:
            return False
        return current_discount

    # compare priorities of current and new discount
    def get_more_important_discount(self, current_discount):
        return self.discount if int(self.discount.priority.value) < int(current_discount.priority.value) else current_discount

    # update new discount value for one product or many products objects
    def update_discount(self, dict):
        if 'product' in dict:
            product = dict['product']
            product.discounted_price = product.get_discounted_price(self.discount.value)
            product.save()
        elif 'products' in dict:
            products = dict['products']
            for product in products:
                product.discounted_price = product.get_discounted_price(self.discount.value)
                product.save()

    def set_discount_for_discounted_products(self, discounted_products):
        for product in discounted_products:
            current_discount = self.get_current_product_discount(product)
            right_discount = self.get_more_important_discount(current_discount)
            if right_discount.id == self.discount.id:
                dict = {'product': product}
                self.update_discount(dict)
            else:
                print('DJANGOTEST: There is disount with higher priority - {}'.format(right_discount))

    # set discount for products
    def set_discounted_price(self):

        # get products with and without discount
        not_discounted_products = self.queryset.filter(discounted_price=None)
        discounted_products = self.queryset.exclude(id__in=[product.id for product in not_discounted_products])

        # 1. no need to check logic/condition for not discounted products
        if not_discounted_products:
            products = {'products': not_discounted_products}
            self.update_discount(products)
        if discounted_products:
            self.set_discount_for_discounted_products(discounted_products)

    def create_queryset(self):
        from .models import Product
        # standard discounts e.g. department, category
        if self.lookup_field:
            self.queryset = Product.objects.filter(**{self.lookup_field: self.discount.set_id})

        # custom discounts e.g. list of random special products imported via forms
        elif self.discount.set_id:
            from .models import DiscountCustom
            try:
                custom_set = DiscountCustom.objects.get(id=self.discount.set_id)
            except DiscountCustom.DoesNotExist:
                return False
            product_list = custom_set.get_products_id()
            self.queryset = Product.objects.filter(id__in=product_list)

        # global discounts for all products
        else:
            self.queryset = Product.objects.all()

        return True if self.queryset else False

    def create_discount_lines(self):
        if self.queryset:
            from .models import DiscountLine
            for product in self.queryset:
                discount_line = DiscountLine(discount=self.discount, product=product)
                discount_line.save()
            return True
        else:
            return False

    def calculate_discount(self, discount):

        self.discount = discount
        self.now = timezone.now()

        # assign field filter for queryset
        self.lookup_field = self.discount.type.lookup_field
        can_be_calculated = self.check_if_can_be_calculated()

        if can_be_calculated:

            # 1. Create discount's queryset of product objects
            queryset = self.create_queryset()

            if queryset:

                # 2. Create DiscountLines objects for discount's products
                discount_lines = self.create_discount_lines()

                if discount_lines:

                    # 3. Set discounted price for discount's products
                    self.set_discounted_price()

                    return True

        return False

    def close_discount(self, discount):
        pass
