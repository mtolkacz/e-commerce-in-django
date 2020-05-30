from .models import Sale


class SaleManager:
    def __init__(self, order):
        self.order = order

    def create_sale(self):
        if self.order:
            items = self.order.items.all()
            for item in items:
                product_price = item.product.discounted_price if item.product.discounted_price else item.product.price
                promo_code = self.order.promo_code if self.order.promo_code else None
                sale = Sale(product=item.product, price=product_price, promo_code=promo_code)
                sale.save()



