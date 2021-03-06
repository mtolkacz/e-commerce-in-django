from decimal import Decimal

from cart.models import PromoCode, PromoCodeUsage


class PromoCodeManager:
    def __init__(self, request, order, code):
        self.request = request
        self.user = request.user
        self.code = code
        self.promo_code = self.get_promo_code_object()
        self.order = order

    def get_promo_code_object(self):
        promo_code = None
        if self.code:
            try:
                promo_code = PromoCode.objects.get(code=self.code, active=True)
            except PromoCode.DoesNotExist:
                pass
        return promo_code

    def is_already_used(self):
        try:
            already_used = PromoCodeUsage.objects.get(user=self.user, promocode=self.promo_code)
        except PromoCodeUsage.DoesNotExist:
            already_used = False
        return already_used

    def meets_requirements(self, total):
        return total.amount > Decimal(self.promo_code.minimum_order_value)

    def get_context_data(self, order):
        data = {}
        cart_total = order.get_cart_total()
        data['promo_value'] = f"-{str(order.get_promo_code_value())}"
        data['cart_total_value'] = str(cart_total)
        data['cart_id'] = str(self.order.id)
        data['message'] = 'Promo code added successfully'
        data['success'] = True
        return data

    def save_code_usage(self):
        promo_usage = PromoCodeUsage(user=self.order.owner, order=self.order, promocode=self.promo_code)
        promo_usage.save()