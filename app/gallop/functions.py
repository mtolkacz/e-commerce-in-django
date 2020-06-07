from accounts.models import User


def get_user_object(request):
    user = None
    if request:
        try:
            user = User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            pass
    return user


def update_user_from_form(form, user, request=False):
    if not form.is_valid():
        return False
    else:
        fields_to_update = []

        # todo probably not to elegant approach, but potentially save time on db operations
        if user.first_name != form.cleaned_data['first_name']:
            user.first_name = form.cleaned_data['first_name']
            fields_to_update.append('first_name')
        if user.last_name != form.cleaned_data['last_name']:
            user.last_name = form.cleaned_data['last_name']
            fields_to_update.append('last_name')
        if user.address_1 != form.cleaned_data['address_1']:
            user.address_1 = form.cleaned_data['address_1']
            fields_to_update.append('address_1')
        if user.address_2 != form.cleaned_data['address_2']:
            print(f'DJANGOTEST: 1 {user.address_2}, {form.cleaned_data["address_2"]}')
            user.address_2 = form.cleaned_data['address_2']
            fields_to_update.append('address_2')
            print(f'DJANGOTEST: {fields_to_update}')
        if user.country != form.cleaned_data['country']:
            user.country = form.cleaned_data['country']
            fields_to_update.append('country')
        if user.voivodeship != form.cleaned_data['voivodeship']:
            user.voivodeship = form.cleaned_data['voivodeship']
            fields_to_update.append('voivodeship')
        if user.city != form.cleaned_data['city']:
            user.city = form.cleaned_data['city']
            fields_to_update.append('city')
        if user.zip_code != form.cleaned_data['zip_code']:
            user.zip_code = form.cleaned_data['zip_code']
            fields_to_update.append('zip_code')
        if request and 'picture' in request.FILES:
            user.picture = request.FILES['picture']
            fields_to_update.append('picture')

        print(f'DJANGOTEST: {len(fields_to_update)}')

        if len(fields_to_update):
            user.save(update_fields=fields_to_update)
            return True
        else:
            False


def create_user_from_form(form):
    # Save form but not commit yet
    user = form.save(commit=False)

    # Set deactivated till mail confirmation
    user.is_active = False

    # Create new user
    user.save()

    return user