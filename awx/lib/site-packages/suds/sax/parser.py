# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

"""
The sax module contains a collection of classes that provide a
(D)ocument (O)bject (M)odel representation of an XML document.
The goal is to provide an easy, intuative interface for managing XML
documents.  Although, the term, DOM, is used above, this model is
B{far} better.

XML namespaces in suds are represented using a (2) element tuple
containing the prefix and the URI.  Eg: I{('tns', 'http://myns')}

"""

from logging import getLogger
import suds.metrics
from suds import *
from suds.sax import *
from suds.sax.document import Document
from suds.sax.element import Element
from suds.sax.text import Text
from suds.sax.attribute import Attribute
from xml.sax import make_parser, InputSource, ContentHandler
from xml.sax.handler import feature_external_ges
from cStringIO import StringIO

log = getLogger(__name__)


class Handler(ContentHandler):
    """ sax hanlder """
    
    def __init__(self):
        self.nodes = [Document()]
 
    def startElement(self, name, attrs):
        top = self.top()
        node = Element(unicode(name), parent=top)
        for a in attrs.getNames():
            n = unicode(a)
            v = unicode(attrs.getValue(a))
            attribute = Attribute(n,v)
            if self.mapPrefix(node, attribute):
                continue
            node.append(attribute)
        node.charbuffer = []
        top.append(node)
        self.push(node)
        
    def mapPrefix(self, node, attribute):
        skip = False
        if attribute.name == 'xmlns':
            if len(attribute.value):
                node.expns = unicode(attribute.value)
            skip = True
        elif attribute.prefix == 'xmlns':
            prefix = attribute.name
            node.nsprefixes[prefix] = unicode(attribute.value)
            skip = True
        return skip
 
    def endElement(self, name):
        name = unicode(name)
        current = self.top()
        if len(current.charbuffer):
            current.text = Text(u''.join(current.charbuffer))
        del current.charbuffer
        if len(current):
            current.trim()
        currentqname = current.qname()
        if name == currentqname:
            self.pop()
        else:
            raise Exception('malformed document')
 
    def characters(self, content):
        text = unicode(content)
        node = self.top()
        node.charbuffer.append(text)

    def push(self, node):
        self.nodes.append(node)
        return node

    def pop(self):
        return self.nodes.pop()
 
    def top(self):
        return self.nodes[len(self.nodes)-1]


class Parser:
    """ SAX Parser """
    
    @classmethod
    def saxparser(cls):
        p = make_parser()
        p.setFeature(feature_external_ges, 0)
        h = Handler()
        p.setContentHandler(h)
        return (p, h)
        
    def parse(self, file=None, string=None):
        """
        SAX parse XML text.
        @param file: Parse a python I{file-like} object.
        @type file: I{file-like} object.
        @param string: Parse string XML.
        @type string: str
        """
        timer = metrics.Timer()
        timer.start()
        sax, handler = self.saxparser()
        if file is not None:
            sax.parse(file)
            timer.stop()
            metrics.log.debug('sax (%s) duration: %s', file, timer)
            return handler.nodes[0]
        if string is not None:
            source = InputSource(None)
            source.setByteStream(StringIO(string))
            sax.parse(source)
            timer.stop()
            metrics.log.debug('%s\nsax duration: %s', string, timer)
            return handler.nodes[0]