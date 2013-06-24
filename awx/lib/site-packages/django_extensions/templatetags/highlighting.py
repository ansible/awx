"""
Similar to syntax_color.py but this is intended more for being able to
copy+paste actual code into your Django templates without needing to
escape or anything crazy.

http://lobstertech.com/2008/aug/30/django_syntax_highlight_template_tag/

Example:

 {% load highlighting %}

 <style>
 @import url("http://lobstertech.com/media/css/highlight.css");
 .highlight { background: #f8f8f8; }
 .highlight { font-size: 11px; margin: 1em; border: 1px solid #ccc;
              border-left: 3px solid #F90; padding: 0; }
 .highlight pre { padding: 1em; overflow: auto; line-height: 120%; margin: 0; }
 .predesc { margin: 1.5em 1.5em -2.5em 1em; text-align: right;
            font: bold 12px Tahoma, Arial, sans-serif;
            letter-spacing: 1px; color: #333; }
 </style>

 <h2>check out this code</h2>

 {% highlight 'python' 'Excerpt: blah.py' %}
 def need_food(self):
     print("Love is <colder> than &death&")
 {% endhighlight %}

"""

from pygments import highlight as pyghighlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from django import template
from django.template import Template, Context, Node, Variable, TemplateSyntaxError
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
@stringfilter
def parse_template(value):
    return mark_safe(Template(value).render(Context()))
parse_template.is_safe = True


class CodeNode(Node):
    def __init__(self, language, nodelist, name=''):
        self.language = Variable(language)
        self.nodelist = nodelist
        if name:
            self.name = Variable(name)
        else:
            self.name = None

    def render(self, context):
        code = self.nodelist.render(context).strip()
        lexer = get_lexer_by_name(self.language.resolve(context))
        formatter = HtmlFormatter(linenos=False)
        html = ""
        if self.name:
            name = self.name.resolve(context)
            html = '<div class="predesc"><span>%s</span></div>' % (name)
        return html + pyghighlight(code, lexer, formatter)


@register.tag
def highlight(parser, token):
    """
    Allows you to put a highlighted source code <pre> block in your code.
    This takes two arguments, the language and a little explaination message
    that will be generated before the code.  The second argument is optional.

    Your code will be fed through pygments so you can use any language it
    supports.

    {% load highlighting %}
    {% highlight 'python' 'Excerpt: blah.py' %}
    def need_food(self):
        print("Love is colder than death")
    {% endhighlight %}
    """
    nodelist = parser.parse(('endhighlight',))
    parser.delete_first_token()
    bits = token.split_contents()[1:]
    if len(bits) < 1:
        raise TemplateSyntaxError("'highlight' statement requires an argument")
    return CodeNode(bits[0], nodelist, *bits[1:])
