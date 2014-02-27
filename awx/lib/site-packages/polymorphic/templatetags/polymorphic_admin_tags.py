from django.template import Library, Node, TemplateSyntaxError
from django.utils import six

register = Library()


class BreadcrumbScope(Node):
    def __init__(self, base_opts, nodelist):
        self.base_opts = base_opts
        self.nodelist = nodelist   # Note, takes advantage of Node.child_nodelists

    @classmethod
    def parse(cls, parser, token):
        bits = token.split_contents()
        if len(bits) == 2:
            (tagname, base_opts) = bits
            base_opts = parser.compile_filter(base_opts)
            nodelist = parser.parse(('endbreadcrumb_scope',))
            parser.delete_first_token()

            return cls(
                base_opts=base_opts,
                nodelist=nodelist
            )
        else:
            raise TemplateSyntaxError("{0} tag expects 1 argument".format(token.contents[0]))


    def render(self, context):
        # app_label is really hard to overwrite in the standard Django ModelAdmin.
        # To insert it in the template, the entire render_change_form() and delete_view() have to copied and adjusted.
        # Instead, have an assignment tag that inserts that in the template.
        base_opts = self.base_opts.resolve(context)
        new_vars = {}
        if base_opts and not isinstance(base_opts, six.string_types):
            new_vars = {
                'app_label': base_opts.app_label,  # What this is all about
                'opts': base_opts,
            }

        new_scope = context.push()
        new_scope.update(new_vars)
        html = self.nodelist.render(context)
        context.pop()
        return html


@register.tag
def breadcrumb_scope(parser, token):
    """
    Easily allow the breadcrumb to be generated in the admin change templates.
    """
    return BreadcrumbScope.parse(parser, token)
