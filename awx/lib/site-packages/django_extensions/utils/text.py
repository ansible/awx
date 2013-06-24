import six

from django.utils.functional import allow_lazy

# conditional import, force_unicode was renamed in Django 1.5
try:
    from django.utils.encoding import force_unicode  # NOQA
except ImportError:
    from django.utils.encoding import force_text as force_unicode  # NOQA


def truncate_letters(s, num):
    """
    truncates a string to a number of letters, similar to truncate_words
    """
    s = force_unicode(s)
    length = int(num)
    if len(s) > length:
        s = s[:length]
        if not s.endswith('...'):
            s += '...'
    return s
truncate_letters = allow_lazy(truncate_letters, six.text_type)
