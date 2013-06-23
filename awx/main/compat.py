'''
Compability library for support of both Django 1.4.x and Django 1.5.x.
'''

try:
    from django.utils.html import format_html
except ImportError:
    from django.utils.html import conditional_escape
    from django.utils.safestring import mark_safe
    def format_html(format_string, *args, **kwargs):
        args_safe = map(conditional_escape, args)
        kwargs_safe = dict([(k, conditional_escape(v)) for (k, v) in
                            kwargs.items()])
        return mark_safe(format_string.format(*args_safe, **kwargs_safe))

try:
    from django.utils.log import RequireDebugTrue
except ImportError:
    import logging
    from django.conf import settings
    class RequireDebugTrue(logging.Filter):
        def filter(self, record):
            return settings.DEBUG
