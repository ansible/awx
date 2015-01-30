"""
HeaderID Extension for Python-Markdown
======================================

Auto-generate id attributes for HTML headers.

See <https://pythonhosted.org/Markdown/extensions/header_id.html> 
for documentation.

Original code Copyright 2007-2011 [Waylan Limberg](http://achinghead.com/).

All changes Copyright 2011-2014 The Python Markdown Project

License: [BSD](http://www.opensource.org/licenses/bsd-license.php) 

"""

from __future__ import absolute_import
from __future__ import unicode_literals
from . import Extension
from ..treeprocessors import Treeprocessor
from ..util import HTML_PLACEHOLDER_RE, parseBoolValue
import re
import logging
import unicodedata

logger = logging.getLogger('MARKDOWN')

IDCOUNT_RE = re.compile(r'^(.*)_([0-9]+)$')


def slugify(value, separator):
    """ Slugify a string, to make it URL friendly. """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub('[^\w\s-]', '', value.decode('ascii')).strip().lower()
    return re.sub('[%s\s]+' % separator, separator, value)


def unique(id, ids):
    """ Ensure id is unique in set of ids. Append '_1', '_2'... if not """
    while id in ids or not id:
        m = IDCOUNT_RE.match(id)
        if m:
            id = '%s_%d'% (m.group(1), int(m.group(2))+1)
        else:
            id = '%s_%d'% (id, 1)
    ids.add(id)
    return id


def itertext(elem):
    """ Loop through all children and return text only. 
    
    Reimplements method of same name added to ElementTree in Python 2.7
    
    """
    if elem.text:
        yield elem.text
    for e in elem:
        for s in itertext(e):
            yield s
        if e.tail:
            yield e.tail


def stashedHTML2text(text, md):
    """ Extract raw HTML, reduce to plain text and swap with placeholder. """
    def _html_sub(m):
        """ Substitute raw html with plain text. """
        try:
            raw, safe = md.htmlStash.rawHtmlBlocks[int(m.group(1))]
        except (IndexError, TypeError):
            return m.group(0)
        if md.safeMode and not safe:
            return ''
        # Strip out tags and entities - leaveing text
        return re.sub(r'(<[^>]+>)|(&[\#a-zA-Z0-9]+;)', '', raw)

    return HTML_PLACEHOLDER_RE.sub(_html_sub, text)


class HeaderIdTreeprocessor(Treeprocessor):
    """ Assign IDs to headers. """

    IDs = set()

    def run(self, doc):
        start_level, force_id = self._get_meta()
        slugify = self.config['slugify']
        sep = self.config['separator']
        for elem in doc.getiterator():
            if elem.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if force_id:
                    if "id" in elem.attrib:
                        id = elem.get('id')
                    else:
                        id = stashedHTML2text(''.join(itertext(elem)), self.md)
                        id = slugify(id, sep)
                    elem.set('id', unique(id, self.IDs))
                if start_level:
                    level = int(elem.tag[-1]) + start_level
                    if level > 6:
                        level = 6
                    elem.tag = 'h%d' % level


    def _get_meta(self):
        """ Return meta data suported by this ext as a tuple """
        level = int(self.config['level']) - 1
        force = parseBoolValue(self.config['forceid'])
        if hasattr(self.md, 'Meta'):
            if 'header_level' in self.md.Meta:
                level = int(self.md.Meta['header_level'][0]) - 1
            if 'header_forceid' in self.md.Meta: 
                force = parseBoolValue(self.md.Meta['header_forceid'][0])
        return level, force


class HeaderIdExtension(Extension):
    def __init__(self, *args, **kwargs):
        # set defaults
        self.config = {
                'level' : ['1', 'Base level for headers.'],
                'forceid' : ['True', 'Force all headers to have an id.'],
                'separator' : ['-', 'Word separator.'],
                'slugify' : [slugify, 'Callable to generate anchors'], 
            }

        super(HeaderIdExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = HeaderIdTreeprocessor()
        self.processor.md = md
        self.processor.config = self.getConfigs()
        if 'attr_list' in md.treeprocessors.keys():
            # insert after attr_list treeprocessor
            md.treeprocessors.add('headerid', self.processor, '>attr_list')
        else:
            # insert after 'prettify' treeprocessor.
            md.treeprocessors.add('headerid', self.processor, '>prettify')

    def reset(self):
        self.processor.IDs = set()


def makeExtension(*args, **kwargs):
    return HeaderIdExtension(*args, **kwargs)

