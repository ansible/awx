import re
from django import template

register = template.Library()

CONSONANT_SOUND = re.compile(r'''one(![ir])''', re.IGNORECASE|re.VERBOSE)  # noqa
VOWEL_SOUND = re.compile(r'''[aeio]|u([aeiou]|[^n][^aeiou]|ni[^dmnl]|nil[^l])|h(ier|onest|onou?r|ors\b|our(!i))|[fhlmnrsx]\b''', re.IGNORECASE|re.VERBOSE)  # noqa


@register.filter
def anora(text):
    # https://pypi.python.org/pypi/anora
    # < 10 lines of BSD-3 code, not worth a dependency
    anora = 'an' if not CONSONANT_SOUND.match(text) and VOWEL_SOUND.match(text) else 'a'
    return anora + ' ' + text


@register.tag(name='ifmeth')
def ifmeth(parser, token):
    """
    Used to mark template blocks for Swagger/OpenAPI output.
    If the specified method matches the *current* method in Swagger/OpenAPI
    generation, show the block.  Otherwise, the block is omitted.

        {% ifmeth GET %}
        Make a GET request to...
        {% endifmeth %}

        {% ifmeth PUT PATCH %}
        Make a PUT or PATCH request to...
        {% endifmeth %}
    """
    allowed_methods = [m.upper() for m in token.split_contents()[1:]]
    nodelist = parser.parse(('endifmeth',))
    parser.delete_first_token()
    return MethodFilterNode(allowed_methods, nodelist)


class MethodFilterNode(template.Node):
    def __init__(self, allowed_methods, nodelist):
        self.allowed_methods = allowed_methods
        self.nodelist = nodelist

    def render(self, context):
        swagger_method = context.get('swagger_method')
        if not swagger_method or swagger_method.upper() in self.allowed_methods:
            return self.nodelist.render(context)
        return ''
