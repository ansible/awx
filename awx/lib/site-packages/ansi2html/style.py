#    This file is part of ansi2html.
#    Copyright (C) 2012  Kuno Woudt <kuno@frob.nl>
#    Copyright (C) 2013  Sebastian Pipping <sebastian@pipping.org>
#
#    This program is free software: you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see
#    <http://www.gnu.org/licenses/>.

import sys


class Rule(object):

    def __init__(self, klass, **kw):

        self.klass = klass
        self.kw = '; '.join([(k.replace('_', '-')+': '+kw[k])
                             for k in sorted(kw.keys())]).strip()

    def __str__(self):
        return '%s { %s; }' % (self.klass, self.kw)


def index(r, g, b):
    return str(16 + (r * 36) + (g * 6) + b)


def color(r, g, b):
    return "#%.2x%.2x%.2x" % (r * 42, g * 42, b * 42)


def level(grey):
    return "#%.2x%.2x%.2x" % (((grey * 10) + 8,) * 3)


def index2(grey):
    return str(232 + grey)

# http://en.wikipedia.org/wiki/ANSI_escape_code#Colors
SCHEME = { # black red green brown/yellow blue magenta cyan grey/white
    'ansi2html': ("#000316", "#aa0000", "#00aa00", "#aa5500", "#0000aa",
                  "#E850A8", "#00aaaa", "#F5F1DE"),
    'xterm': ("#000000", "#cd0000", "#00cd00", "#cdcd00", "#0000ee",
              "#cd00cd", "#00cdcd", "#e5e5e5"),
    'xterm-bright': ("#7f7f7f", "#ff0000", "#00ff00", "#ffff00", "#5c5cff",
                     "#ff00ff", "#00ffff", "#ffffff"),
    'osx': ("#000000", "#c23621", "#25bc24", "#adad27", "#492ee1",
            "#d338d3", "#33bbc8", "#cbcccd"),

    # http://ethanschoonover.com/solarized
    'solarized': ("#262626", "#d70000", "#5f8700", "#af8700", "#0087ff",
                  "#af005f", "#00afaf", "#e4e4e4"),
    }

def get_styles(dark_bg=True, scheme='ansi2html'):

    css = [
        Rule('.body_foreground', color=('#000000', '#AAAAAA')[dark_bg]),
        Rule('.body_background', background_color=('#AAAAAA', '#000000')[dark_bg]),
        Rule('.body_foreground > .bold,.bold > .body_foreground, body.body_foreground > pre > .bold',
             color=('#000000', '#FFFFFF')[dark_bg], font_weight=('bold', 'normal')[dark_bg]),
        Rule('.inv_foreground', color=('#000000', '#FFFFFF')[not dark_bg]),
        Rule('.inv_background', background_color=('#AAAAAA', '#000000')[not dark_bg]),
        Rule('.ansi1', font_weight='bold'),
        Rule('.ansi2', font_weight='lighter'),
        Rule('.ansi3', font_style='italic'),
        Rule('.ansi4', text_decoration='underline'),
        Rule('.ansi5', text_decoration='blink'),
        Rule('.ansi6', text_decoration='blink'),
        Rule('.ansi8', visibility='hidden'),
        Rule('.ansi9', text_decoration='line-through'),
        ]

    # set palette
    pal = SCHEME[scheme]
    for _index in range(8):
        css.append(Rule('.ansi3%s' % _index, color=pal[_index]))
        css.append(Rule('.inv3%s' % _index, background_color=pal[_index]))
    for _index in range(8):
        css.append(Rule('.ansi4%s' % _index, background_color=pal[_index]))
        css.append(Rule('.inv4%s' % _index, color=pal[_index]))

    # css.append("/* Define the explicit color codes (obnoxious) */\n\n")

    for green in range(0, 6):
        for red in range(0, 6):
            for blue in range(0, 6):
                css.append(Rule(".ansi38-%s" % index(red, green, blue),
                                color=color(red, green, blue)))
                css.append(Rule(".inv38-%s" % index(red, green, blue),
                                background=color(red, green, blue)))
                css.append(Rule(".ansi48-%s" % index(red, green, blue),
                                background=color(red, green, blue)))
                css.append(Rule(".inv48-%s" % index(red, green, blue),
                                color=color(red, green, blue)))

    for grey in range(0, 24):
        css.append(Rule('.ansi38-%s' % index2(grey), color=level(grey)))
        css.append(Rule('.inv38-%s' % index2(grey), background=level(grey)))
        css.append(Rule('.ansi48-%s' % index2(grey), background=level(grey)))
        css.append(Rule('.inv48-%s' % index2(grey), color=level(grey)))

    return css
