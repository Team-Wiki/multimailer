import hashlib

from django import template

register = template.Library()

@register.filter(name='gravatar_image')
def gravatar_image(value, arg):
    email = bytes(str(value).strip().lower(), 'utf-8')
    hash = hashlib.md5(email).hexdigest()
    return 'https://www.gravatar.com/avatar/' + hash + '?s=' + str(arg) + '&d=identicon'

