from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from products.models import Product, ProductRating


@require_http_methods(['POST'])
@login_required
def rating(request):
    data = {}
    user = request.user
    prod_id = request.POST.get('prod_id', None)
    try:
        score = int(request.POST.get('score', None))
    except(TypeError, ValueError, OverflowError):
        score = None
    if prod_id and score:
        try:
            product = Product.objects.get(id=prod_id)
        except Product.DoesNotExist:
            product = None
        if product:
            new_rating = ProductRating(user=user, product=product, score=score)
            new_rating.save()
            rating_dict = {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'thumbnail': {'url': product.thumbnail.url},
                    'get_absolute_url': product.get_absolute_url(),
                },
                'score': new_rating.score,
            }
            data['rating'] = rating_dict
    return JsonResponse(data)
