"""
Sets up the terminal color scheme.
"""

from django.core.management import color
from django.utils import termcolors


def color_style():
    style = color.color_style()
    if color.supports_color():
        style.URL = termcolors.make_style(fg='green', opts=('bold',))
        style.MODULE = termcolors.make_style(fg='yellow')
        style.MODULE_NAME = termcolors.make_style(opts=('bold',))
        style.URL_NAME = termcolors.make_style(fg='red')
    return style
