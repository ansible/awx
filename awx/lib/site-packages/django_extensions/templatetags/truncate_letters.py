import django
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


def truncateletters(value, arg):
    """
    Truncates a string after a certain number of letters

    Argument: Number of letters to truncate after
    """
    from django_extensions.utils.text import truncate_letters
    try:
        length = int(arg)
    except ValueError:  # invalid literal for int()
        return value  # Fail silently
    return truncate_letters(value, length)

if django.get_version() >= "1.4":
    truncateletters = stringfilter(truncateletters)
    register.filter(truncateletters, is_safe=True)
else:
    truncateletters.is_safe = True
    truncateletters = stringfilter(truncateletters)
    register.filter(truncateletters)

