from accounts.models import User


def get_user_object(request):
    user = None
    if request:
        try:
            user = User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            pass
    return user

