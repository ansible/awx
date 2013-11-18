from django import template

register = template.Library()


class IndentByNode(template.Node):
    def __init__(self, nodelist, indent_level, if_statement):
        self.nodelist = nodelist
        self.indent_level = template.Variable(indent_level)
        if if_statement:
            self.if_statement = template.Variable(if_statement)
        else:
            self.if_statement = None

    def render(self, context):
        indent_level = self.indent_level.resolve(context)
        if self.if_statement:
            try:
                if_statement = bool(self.if_statement.resolve(context))
            except template.VariableDoesNotExist:
                if_statement = False
        else:
            if_statement = True
        output = self.nodelist.render(context)
        if if_statement:
            indent = " " * indent_level
            output = indent + indent.join(output.splitlines(True))
        return output


def indentby(parser, token):
    """
    Adds indentation to text between the tags by the given indentation level.

    {% indentby <indent_level> [if <statement>] %}
    ...
    {% endindentby %}

    Arguments:
      indent_level - Number of spaces to indent text with.
      statement - Only apply indent_level if the boolean statement evalutates to True.
    """
    args = token.split_contents()
    largs = len(args)
    if largs not in (2, 4):
        raise template.TemplateSyntaxError("%r tag requires 1 or 3 arguments")
    indent_level = args[1]
    if_statement = None
    if largs == 4:
        if_statement = args[3]
    nodelist = parser.parse(('endindentby', ))
    parser.delete_first_token()
    return IndentByNode(nodelist, indent_level, if_statement)

indentby = register.tag(indentby)
