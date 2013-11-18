import json

from django import template
from django.utils.safestring import mark_safe
from jsonfield.utils import TZAwareJSONEncoder

register = template.Library()

@register.filter
def jsonify(value):
    if getattr(value, 'all', False):
        value = list(value)
    return mark_safe(json.dumps(value, cls=TZAwareJSONEncoder))
