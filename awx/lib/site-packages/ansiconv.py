"""
Converts ANSI coded text and converts it to either plain text
or to HTML.
"""
import re

supported_sgr_codes = [1, 3, 4, 9, 30, 31, 32, 33, 34, 35, 36, 37, 40, 41, 42,
                       43, 44, 45, 46, 47]


def to_plain(ansi):
    """Takes the given string and strips all ANSI codes out.

    :param ansi: The string to strip
    :return: The stripped string
    """
    return re.sub(r'\x1B\[[0-9;]*[ABCDEFGHJKSTfmnsulh]', '', ansi)


def to_html(ansi, replace_newline=False):
    """Converts the given ANSI string to HTML

    If `replace_newline` is set to True, then all newlines will be
    replaced with <br />.

    :param ansi: The ANSI text.
    :param replace_newline: Whether to replace newlines with HTML.
    :return: The resulting HTML string.
    """
    blocks = ansi.split('\x1B')
    parsed_blocks = []
    for block in blocks:
        command, text = _block_to_html(block)

        # The command "A" means move the cursor up, so we emulate that here.
        if command == 'A' and len(parsed_blocks) > 0:
            parsed_blocks.pop()
            while len(parsed_blocks) > 0 and '\n' not in parsed_blocks[-1]:
                parsed_blocks.pop()

        parsed_blocks.append(text)

    text = ''.join(parsed_blocks)

    if replace_newline:
        text = text.replace('\n', '<br />\n')

    return text


def base_css(dark=True):
    """Some base CSS with all of the default ANSI styles/colors.

    :param dark: Whether background should be dark or light.
    :return: A string of CSS
    """
    return "\n".join([
        css_rule('.ansi_fore', color=('#000000', '#FFFFFF')[dark]),
        css_rule('.ansi_back', background_color=('#FFFFFF', '#000000')[dark]),
        css_rule('.ansi1', font_weight='bold'),
        css_rule('.ansi3', font_weight='italic'),
        css_rule('.ansi4', text_decoration='underline'),
        css_rule('.ansi9', text_decoration='line-through'),
        css_rule('.ansi30', color="#000000"),
        css_rule('.ansi31', color="#FF0000"),
        css_rule('.ansi32', color="#00FF00"),
        css_rule('.ansi33', color="#FFFF00"),
        css_rule('.ansi34', color="#0000FF"),
        css_rule('.ansi35', color="#FF00FF"),
        css_rule('.ansi36', color="#00FFFF"),
        css_rule('.ansi37', color="#FFFFFF"),
        css_rule('.ansi40', background_color="#000000"),
        css_rule('.ansi41', background_color="#FF0000"),
        css_rule('.ansi42', background_color="#00FF00"),
        css_rule('.ansi43', background_color="#FFFF00"),
        css_rule('.ansi44', background_color="#0000FF"),
        css_rule('.ansi45', background_color="#FF00FF"),
        css_rule('.ansi46', background_color="#00FFFF"),
        css_rule('.ansi47', background_color="#FFFFFF")
    ])


def css_rule(class_name, **properties):
    """Creates a CSS rule string.

    The named parameters are used as the css properties.  Underscores
    are converted to hyphens.

    :param class_name: The CSS class name
    :param properties: The properties sent as named params.
    :return: The CSS string
    """
    prop_str = lambda name, val: name.replace('_', '-') + ': ' + val
    return '{0} {{ {1}; }}'.format(
        class_name,
        '; '.join([prop_str(prop, properties[prop]) for prop in properties])
    )


def _block_to_html(text):
    """Converts the given block of ANSI coded text to HTML.

    The text is only given back as HTML if the ANSI code is at the
    beginning of the string (e.g. "[0;33mFoobar")

    :param text: The text block to convert.
    :return: The text as HTML
    """
    match = re.match(r'^\[(?P<code>\d+(?:;\d+)*)?(?P<command>[Am])', text)
    if match is None:
        return None, text

    command = match.group('command')
    text = text[match.end():]

    if match.group('code') is None:
        return command, text

    classes = []
    for code in match.group('code').split(';'):
        if int(code) in supported_sgr_codes:
            classes.append('ansi{0}'.format(code))

    if classes:
        text = '<span class="{0}">{1}</span>'.format(' '.join(classes), text)

    return command, text
