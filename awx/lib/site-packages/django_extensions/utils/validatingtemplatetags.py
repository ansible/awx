from django.template.base import Library, Node
from django.template import defaulttags
from django.templatetags import future
register = Library()

error_on_old_style_url_tag = False
new_style_url_tag = False
errors = []


def before_new_template(force_new_urls):
    """Reset state ready for new template"""
    global new_style_url_tag, error_on_old_style_url_tag, errors
    new_style_url_tag = False
    error_on_old_style_url_tag = force_new_urls
    errors = []


def get_template_errors():
    return errors


# Disable extends and include as they are not needed, slow parsing down, and cause duplicate errors
class NoOpNode(Node):
    def render(self, context):
        return ''


@register.tag
def extends(parser, token):
    return NoOpNode()


@register.tag
def include(parser, token):
    return NoOpNode()


# We replace load to determine whether new style urls are in use and re-patch url after
# a future version is loaded
@register.tag
def load(parser, token):
    global new_style_url_tag
    bits = token.contents.split()

    reloaded_url_tag = False
    if len(bits) >= 4 and bits[-2] == "from" and bits[-1] == "future":
        for name in bits[1:-2]:
            if name == "url":
                new_style_url_tag = True
                reloaded_url_tag = True

    try:
        return defaulttags.load(parser, token)
    finally:
        if reloaded_url_tag:
            parser.tags['url'] = new_style_url


@register.tag(name='url')
def old_style_url(parser, token):
    global error_on_old_style_url_tag

    bits = token.split_contents()
    view = bits[1]

    if error_on_old_style_url_tag:
        _error("Old style url tag used (only reported once per file): {%% %s %%}" % (" ".join(bits)), token)
        error_on_old_style_url_tag = False

    if view[0] in "\"'" and view[0] == view[-1]:
        _error("Old style url tag with quotes around view name: {%% %s %%}" % (" ".join(bits)), token)

    return defaulttags.url(parser, token)


def new_style_url(parser, token):
    bits = token.split_contents()
    view = bits[1]

    if view[0] not in "\"'" or view[0] != view[-1]:
        _error("New style url tag without quotes around view name: {%% %s %%}" % (" ".join(bits)), token)

    return future.url(parser, token)


def _error(message, token):
    origin, (start, upto) = token.source
    source = origin.reload()
    line = source.count("\n", 0, start) + 1  # 1 based line numbering
    errors.append((origin, line, message))
