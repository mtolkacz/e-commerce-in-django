from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from products.models import Favorites, Product


@require_http_methods(['POST'])
@login_required
def add_favorite(request):
    data = {}
    # user = glp.get_user_object(request)
    prod_id = request.POST.get('prod_id', None)
    if prod_id:
        try:
            product = Product.objects.get(id=prod_id)
        except Product.DoesNotExist:
            product = None
        if product:
            new_fav = Favorites(user=request.user, product=product)
            new_fav.save()
            data['success'] = True
            data['fav_id'] = new_fav.id
    return JsonResponse(data)


@require_http_methods(['POST'])
@login_required
def delete_favorite(request):
    data = {}
    prod_id = request.POST.get('prod_id', None)
    if prod_id:
        try:
            product = Product.objects.get(id=prod_id)
        except Product.DoesNotExist:
            product = None
        if product:
            try:
                obj = Favorites.objects.get(product=product, user=request.user)
            except Favorites.DoesNotExist:
                obj = None
            if obj:
                obj.delete()
                data['success'] = True
    return JsonResponse(data)
