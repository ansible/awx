"""
Table of Contents Extension for Python-Markdown
===============================================

See <https://pythonhosted.org/Markdown/extensions/toc.html> 
for documentation.

Oringinal code Copyright 2008 [Jack Miller](http://codezen.org)

All changes Copyright 2008-2014 The Python Markdown Project

License: [BSD](http://www.opensource.org/licenses/bsd-license.php) 

"""

from __future__ import absolute_import
from __future__ import unicode_literals
from . import Extension
from ..treeprocessors import Treeprocessor
from ..util import etree, parseBoolValue, AMP_SUBSTITUTE
from .headerid import slugify, unique, itertext, stashedHTML2text
import re


def order_toc_list(toc_list):
    """Given an unsorted list with errors and skips, return a nested one.
    [{'level': 1}, {'level': 2}]
    =>
    [{'level': 1, 'children': [{'level': 2, 'children': []}]}]

    A wrong list is also converted:
    [{'level': 2}, {'level': 1}]
    =>
    [{'level': 2, 'children': []}, {'level': 1, 'children': []}]
    """

    ordered_list = []
    if len(toc_list):
        # Initialize everything by processing the first entry
        last = toc_list.pop(0)
        last['children'] = []
        levels = [last['level']]
        ordered_list.append(last)
        parents = []

        # Walk the rest nesting the entries properly
        while toc_list:
            t = toc_list.pop(0)
            current_level = t['level']
            t['children'] = []

            # Reduce depth if current level < last item's level
            if current_level < levels[-1]:
                # Pop last level since we know we are less than it
                levels.pop()

                # Pop parents and levels we are less than or equal to
                to_pop = 0
                for p in reversed(parents):
                    if current_level <= p['level']:
                        to_pop += 1
                    else:
                        break
                if to_pop:
                    levels = levels[:-to_pop]
                    parents = parents[:-to_pop]

                # Note current level as last
                levels.append(current_level)

            # Level is the same, so append to the current parent (if available)
            if current_level == levels[-1]:
                (parents[-1]['children'] if parents else ordered_list).append(t)

            # Current level is > last item's level,
            # So make last item a parent and append current as child
            else:
                last['children'].append(t)
                parents.append(last)
                levels.append(current_level)
            last = t

    return ordered_list


class TocTreeprocessor(Treeprocessor):
    
    # Iterator wrapper to get parent and child all at once
    def iterparent(self, root):
        for parent in root.getiterator():
            for child in parent:
                yield parent, child
    
    def add_anchor(self, c, elem_id): #@ReservedAssignment
        anchor = etree.Element("a")
        anchor.text = c.text
        anchor.attrib["href"] = "#" + elem_id
        anchor.attrib["class"] = "toclink"
        c.text = ""
        for elem in c.getchildren():
            anchor.append(elem)
            c.remove(elem)
        c.append(anchor)

    def add_permalink(self, c, elem_id):
        permalink = etree.Element("a")
        permalink.text = ("%spara;" % AMP_SUBSTITUTE
            if self.use_permalinks is True else self.use_permalinks)
        permalink.attrib["href"] = "#" + elem_id
        permalink.attrib["class"] = "headerlink"
        permalink.attrib["title"] = "Permanent link"
        c.append(permalink)
    
    def build_toc_etree(self, div, toc_list):
        # Add title to the div
        if self.config["title"]:
            header = etree.SubElement(div, "span")
            header.attrib["class"] = "toctitle"
            header.text = self.config["title"]

        def build_etree_ul(toc_list, parent):
            ul = etree.SubElement(parent, "ul")
            for item in toc_list:
                # List item link, to be inserted into the toc div
                li = etree.SubElement(ul, "li")
                link = etree.SubElement(li, "a")
                link.text = item.get('name', '')
                link.attrib["href"] = '#' + item.get('id', '')
                if item['children']:
                    build_etree_ul(item['children'], li)
            return ul
        
        return build_etree_ul(toc_list, div)
        
    def run(self, doc):

        div = etree.Element("div")
        div.attrib["class"] = "toc"
        header_rgx = re.compile("[Hh][123456]")
        
        self.use_anchors = parseBoolValue(self.config["anchorlink"])
        self.use_permalinks = parseBoolValue(self.config["permalink"], False)
        if self.use_permalinks is None:
            self.use_permalinks = self.config["permalink"]
        
        # Get a list of id attributes
        used_ids = set()
        for c in doc.getiterator():
            if "id" in c.attrib:
                used_ids.add(c.attrib["id"])

        toc_list = []
        marker_found = False
        for (p, c) in self.iterparent(doc):
            text = ''.join(itertext(c)).strip()
            if not text:
                continue

            # To keep the output from screwing up the
            # validation by putting a <div> inside of a <p>
            # we actually replace the <p> in its entirety.
            # We do not allow the marker inside a header as that
            # would causes an enless loop of placing a new TOC 
            # inside previously generated TOC.
            if c.text and c.text.strip() == self.config["marker"] and \
               not header_rgx.match(c.tag) and c.tag not in ['pre', 'code']:
                for i in range(len(p)):
                    if p[i] == c:
                        p[i] = div
                        break
                marker_found = True
                            
            if header_rgx.match(c.tag):
                
                # Do not override pre-existing ids 
                if not "id" in c.attrib:
                    elem_id = stashedHTML2text(text, self.markdown)
                    elem_id = unique(self.config["slugify"](elem_id, '-'), used_ids)
                    c.attrib["id"] = elem_id
                else:
                    elem_id = c.attrib["id"]

                tag_level = int(c.tag[-1])
                
                toc_list.append({'level': tag_level,
                    'id': elem_id,
                    'name': text})

                if self.use_anchors:
                    self.add_anchor(c, elem_id)
                if self.use_permalinks:
                    self.add_permalink(c, elem_id)
                
        toc_list_nested = order_toc_list(toc_list)
        self.build_toc_etree(div, toc_list_nested)
        prettify = self.markdown.treeprocessors.get('prettify')
        if prettify: prettify.run(div)
        if not marker_found:
            # serialize and attach to markdown instance.
            toc = self.markdown.serializer(div)
            for pp in self.markdown.postprocessors.values():
                toc = pp.run(toc)
            self.markdown.toc = toc


class TocExtension(Extension):
    
    TreeProcessorClass = TocTreeprocessor
    
    def __init__(self, *args, **kwargs):
        self.config = { 
            "marker" : ["[TOC]", 
                "Text to find and replace with Table of Contents - "
                "Defaults to \"[TOC]\""],
            "slugify" : [slugify,
                "Function to generate anchors based on header text - "
                "Defaults to the headerid ext's slugify function."],
            "title" : ["",
                "Title to insert into TOC <div> - "
                "Defaults to an empty string"],
            "anchorlink" : [0,
                "1 if header should be a self link - "
                "Defaults to 0"],
            "permalink" : [0,
                "1 or link text if a Sphinx-style permalink should be added - "
                "Defaults to 0"]
        }

        super(TocExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        tocext = self.TreeProcessorClass(md)
        tocext.config = self.getConfigs()
        # Headerid ext is set to '>prettify'. With this set to '_end',
        # it should always come after headerid ext (and honor ids assinged 
        # by the header id extension) if both are used. Same goes for 
        # attr_list extension. This must come last because we don't want
        # to redefine ids after toc is created. But we do want toc prettified.
        md.treeprocessors.add("toc", tocext, "_end")


def makeExtension(*args, **kwargs):
    return TocExtension(*args, **kwargs)
