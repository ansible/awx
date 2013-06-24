r"""
Template filter for rendering a string with syntax highlighting.
It relies on Pygments to accomplish this.

Some standard usage examples (from within Django templates).
Coloring a string with the Python lexer:

    {% load syntax_color %}
    {{ code_string|colorize:"python" }}

You may use any lexer in Pygments. The complete list of which
can be found [on the Pygments website][1].

[1]: http://pygments.org/docs/lexers/

You may also have Pygments attempt to guess the correct lexer for
a particular string. However, if may not be able to choose a lexer,
in which case it will simply return the string unmodified. This is
less efficient compared to specifying the lexer to use.

    {{ code_string|colorize }}

You may also render the syntax highlighed text with line numbers.

    {% load syntax_color %}
    {{ some_code|colorize_table:"html+django" }}
    {{ let_pygments_pick_for_this_code|colorize_table }}

Please note that before you can load the ``syntax_color`` template filters
you will need to add the ``django_extensions.utils`` application to the
``INSTALLED_APPS``setting in your project's ``settings.py`` file.
"""

__author__ = 'Will Larson <lethain@gmail.com>'


from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.core.exceptions import ImproperlyConfigured

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name, guess_lexer, ClassNotFound
except ImportError:
    raise ImproperlyConfigured(
        "Please install 'pygments' library to use syntax_color.")

register = template.Library()


@register.simple_tag
def pygments_css():
    return HtmlFormatter().get_style_defs('.highlight')


def generate_pygments_css(path=None):
    if path is None:
        import os
        path = os.path.join(os.getcwd(), 'pygments.css')
    f = open(path, 'w')
    f.write(pygments_css())
    f.close()


def get_lexer(value, arg):
    if arg is None:
        return guess_lexer(value)
    return get_lexer_by_name(arg)


@register.filter(name='colorize')
@stringfilter
def colorize(value, arg=None):
    try:
        return mark_safe(highlight(value, get_lexer(value, arg), HtmlFormatter()))
    except ClassNotFound:
        return value


@register.filter(name='colorize_table')
@stringfilter
def colorize_table(value, arg=None):
    try:
        return mark_safe(highlight(value, get_lexer(value, arg), HtmlFormatter(linenos='table')))
    except ClassNotFound:
        return value


@register.filter(name='colorize_noclasses')
@stringfilter
def colorize_noclasses(value, arg=None):
    try:
        return mark_safe(highlight(value, get_lexer(value, arg), HtmlFormatter(noclasses=True)))
    except ClassNotFound:
        return value
