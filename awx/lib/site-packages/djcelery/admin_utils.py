from __future__ import absolute_import

from pprint import pformat

from django.utils.html import escape

FIXEDWIDTH_STYLE = '''\
<span title="%s" style="font-size: %spt; \
font-family: Menlo, Courier; ">%s</span> \
'''


def attrs(**kwargs):
    def _inner(fun):
        for attr_name, attr_value in kwargs.items():
            setattr(fun, attr_name, attr_value)
        return fun
    return _inner


def display_field(short_description, admin_order_field,
                  allow_tags=True, **kwargs):
    return attrs(short_description=short_description,
                 admin_order_field=admin_order_field,
                 allow_tags=allow_tags, **kwargs)


def action(short_description, **kwargs):
    return attrs(short_description=short_description, **kwargs)


def fixedwidth(field, name=None, pt=6, width=16, maxlen=64, pretty=False):

    @display_field(name or field, field)
    def f(task):
        val = getattr(task, field)
        if pretty:
            val = pformat(val, width=width)
        if val.startswith("u'") or val.startswith('u"'):
            val = val[2:-1]
        shortval = val.replace(',', ',\n')
        shortval = shortval.replace('\n', '|br/|')

        if len(shortval) > maxlen:
            shortval = shortval[:maxlen] + '...'
        styled = FIXEDWIDTH_STYLE % (escape(val[:255]), pt,
                                     escape(shortval))
        return styled.replace('|br/|', '<br/>')
    return f
