from django.utils import timezone


class DiscountManager:
    queryset = None
    discount = None
    now = None
    lookup_field = None

    def __init__(self, discount):
        self.discount = discount
        self.lookup_field = self.discount.type.lookup_field
        self.now = timezone.now()

    def check_if_can_be_processed(self):
        return self.discount.startdate < self.now

    # return current most important product discount line or False if does not exist
    def get_current_discount_of(self, **kwargs):
        try:
            for key, value in kwargs.items():
                product_discount = DiscountLine.objects. \
                    exclude(discount=self.discount).exclude(status=Discount.FINISHED). \
                    filter(**{key: value}). \
                    order_by('discount__priority__value'). \
                    first()
                current_discount = Discount.objects.get(id=product_discount.discount.id) if product_discount else False
        except Discount.DoesNotExist:
            current_discount = None
        return current_discount

    # compare priorities of current and new discount
    # lower priority = more important to choose
    def choose_more_important_discount(self, current_discount):
        return self.discount \
            if int(self.discount.priority.value) < int(current_discount.priority.value) else current_discount

    @staticmethod
    def update_line_status(status, **kwargs):
        discount = kwargs.get('discount')
        product = kwargs['product'] if 'product' in kwargs else Product.objects.get(id=kwargs['product_id'])
        discount_lines = DiscountLine.objects.filter(product=product, discount=discount)
        for discount_line in discount_lines:
            discount_line.update_status(status)

    # activate line and set new price for one or many products
    # dict parameter can contain one product (queryset object or its id)
    # or list of products and its discount to be activated
    def activate_line_and_update_price(self, dict):
        discount = dict['discount']

        if 'products' in dict:
            products = dict['products']
            for product in products:

                # activate discount line
                self.update_line_status(status=DiscountLine.ACTIVE, product=product, discount=discount)

                product.discounted_price = product.get_discounted_price(self.discount.value)
                product.save()
        else:
            try:
                product = [dict['product'] if 'product' in dict else Product.objects.get(id=dict['product_id'])]
            except Product.DoesNotExist:
                raise Exception('Product does not exist')
            else:
                product = product[0] if isinstance(product, list) else product

                # activate discount line
                self.update_line_status(status=DiscountLine.ACTIVE, product=product, discount=discount)

                # update product price
                product.discounted_price = product.get_discounted_price(discount.value)
                product.save()

    def set_discount_for_discounted_products(self, discounted_products):
        new_discount = self.discount
        for product in discounted_products:
            dict = {
                'product': product,
                'discount': new_discount
            }
            current_discount = self.get_current_discount_of(product=product)
            more_important_discount = self.choose_more_important_discount(current_discount) if current_discount else new_discount
            if more_important_discount.id == new_discount.id:
                self.activate_line_and_update_price(dict)
                self.update_line_status(status=DiscountLine.INACTIVE, product=product, discount=current_discount)

    def process_lines(self):

        # get products with and without discount
        not_discounted_products = self.queryset.exclude(discounted_price__isnull=False)
        discounted_products = self.queryset.exclude(id__in=[product.id for product in not_discounted_products])
        # 1. no need to check logic/condition for not discounted products
        if not_discounted_products:
            products = {
                'products': not_discounted_products,
                'discount': self.discount
            }
            self.activate_line_and_update_price(products)
        if discounted_products:
            self.set_discount_for_discounted_products(discounted_products)

    def delete_discount(self):
        # if not Discount.objects.filter(id=self.discount.id)
        return Discount.objects.get(id=self.discount.id).delete()

    def save_product_list(self):
        product_list = ';'.join(map(str, list([int(product[0]) for product in list(self.queryset.values_list('id'))])))
        product_list = DiscountProductList(discount=self.discount, ids=product_list)
        product_list.save()

    def create_product_queryset(self):
        # standard discounts e.g. department, category
        if self.lookup_field:
            self.queryset = Product.objects.filter(**{self.lookup_field: self.discount.set_id})

        # custom discounts e.g. list of random special products imported via forms
        elif self.discount.set_id:
            try:
                custom_set = DiscountCustom.objects.get(id=self.discount.set_id)
            except DiscountCustom.DoesNotExist:
                return False
            product_list = custom_set.get_products_id()
            self.queryset = Product.objects.filter(id__in=product_list)

        # global discounts for all products
        else:
            self.queryset = Product.objects.all()
        try:
            if not self.queryset:
                deleted_discount = self.delete_discount()
                raise Exception('Cannot get queryset. Discount deleted {}'.format(deleted_discount))
        except Exception as e:
            print(e)
        else:
            self.save_product_list()

    def create_lines(self):
        for product in self.queryset:
            discount_line = DiscountLine(discount=self.discount, product=product)
            discount_line.save()

    @staticmethod
    def reset_product_price(**kwargs):
        product = kwargs['product'] if 'product' in kwargs else Product.objects.get(id=kwargs['product_id'])
        product.reset_price()

    def process(self):

        if self.discount.status != Discount.INACTIVE:
            return

        self.discount.update_status(Discount.ACTIVE)

        # 1. Create discount's queryset of product objects
        self.create_product_queryset()

        # 2. Create discount's lines
        self.create_lines()

        # 3. Set discounted price and activate discount lines
        self.process_lines()

    def finish(self):

        discount = self.discount

        if discount.status == Discount.FINISHED:
            return

        # Get discount lines
        lines = DiscountLine.objects.filter(discount=discount)

        # Change discount lines status to Finished
        finished_lines = [line.update_status(DiscountLine.FINISHED) for line in lines] if lines else False

        if finished_lines:

            # Get all products from discount
            try:
                product_list = DiscountProductList.objects.get(discount=discount)
                products = product_list.get_product_list()
            except DiscountProductList.DoesNotExist:
                raise Exception('Cannot get discount product list!')
            else:
                # Activate line and set new price for products if exists different discount
                for product_id in products:
                    next_discount = self.get_current_discount_of(product_id=product_id)
                    dict = {
                        'product_id': product_id,
                        'discount': next_discount
                    }
                    self.activate_line_and_update_price(dict) if next_discount \
                        else self.reset_product_price(product_id=product_id)
                    self.update_line_status(status=DiscountLine.FINISHED, product_id=product_id, discount=discount)

        # Change discount status to Finished
        discount.update_status(Discount.FINISHED)
