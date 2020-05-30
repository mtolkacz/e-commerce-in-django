from .models import PromoCodeUsage, PromoCode
from django.contrib.auth import get_user_model

User = get_user_model()


class PromoCodeManager:
    def __init__(self, request, code):
        self.request = request
        self.user = self.get_user_object()
        self.code = code
        self.promo_code = self.get_promo_code_object()

    def get_user_object(self):
        user = None
        if self.request:
            try:
                user = User.objects.get(id=self.request.user.id)
            except User.DoesNotExist:
                pass
        return user

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
