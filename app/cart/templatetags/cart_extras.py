from django import template

register = template.Library()


@register.simple_tag()
def checkout_url(request):
    from django.urls import reverse
    url = 'https://' + str(request.get_host) + reverse('checkout')
    current_url = request.path()
    return url


@register.simple_tag()
def current_url(request):
    # from django.urls import reverse
    # url = 'https://' + str(request.get_host()) + reverse('checkout')
    current_url = request.path()
    return current_url