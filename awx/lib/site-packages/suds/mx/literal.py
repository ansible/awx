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
Provides literal I{marshaller} classes.
"""

from logging import getLogger
from suds import *
from suds.mx import *
from suds.mx.core import Core
from suds.mx.typer import Typer
from suds.resolver import GraphResolver, Frame
from suds.sax.element import Element
from suds.sudsobject import Factory

log = getLogger(__name__)


#
# Add typed extensions
# type = The expected xsd type
# real = The 'true' XSD type
# ancestry = The 'type' ancestry
#
Content.extensions.append('type')
Content.extensions.append('real')
Content.extensions.append('ancestry')



class Typed(Core):
    """
    A I{typed} marshaller.
    This marshaller is semi-typed as needed to support both
    I{document/literal} and I{rpc/literal} soap message styles.
    @ivar schema: An xsd schema.
    @type schema: L{xsd.schema.Schema}
    @ivar resolver: A schema type resolver.
    @type resolver: L{GraphResolver}
    """

    def __init__(self, schema, xstq=True):
        """
        @param schema: A schema object
        @type schema: L{xsd.schema.Schema}
        @param xstq: The B{x}ml B{s}chema B{t}ype B{q}ualified flag indicates
            that the I{xsi:type} attribute values should be qualified by namespace.
        @type xstq: bool
        """
        Core.__init__(self)
        self.schema = schema
        self.xstq = xstq
        self.resolver = GraphResolver(self.schema)
    
    def reset(self):
        self.resolver.reset()
            
    def start(self, content):
        #
        # Start marshalling the 'content' by ensuring that both the
        # 'content' _and_ the resolver are primed with the XSD type
        # information.  The 'content' value is both translated and
        # sorted based on the XSD type.  Only values that are objects
        # have their attributes sorted.
        #
        log.debug('starting content:\n%s', content)
        if content.type is None:
            name = content.tag
            if name.startswith('_'):
                name = '@'+name[1:]
            content.type = self.resolver.find(name, content.value)
            if content.type is None:
                raise TypeNotFound(content.tag)
        else:
            known = None
            if isinstance(content.value, Object):
                known = self.resolver.known(content.value)
                if known is None:
                    log.debug('object has no type information', content.value)
                    known = content.type
            frame = Frame(content.type, resolved=known)
            self.resolver.push(frame)
        frame = self.resolver.top()
        content.real = frame.resolved
        content.ancestry = frame.ancestry
        self.translate(content)
        self.sort(content)
        if self.skip(content):
            log.debug('skipping (optional) content:\n%s', content)
            self.resolver.pop()
            return False
        else:
            return True
        
    def suspend(self, content):
        #
        # Suspend to process a list content.  Primarily, this
        # involves popping the 'list' content off the resolver's
        # stack so the list items can be marshalled.
        #
        self.resolver.pop()
    
    def resume(self, content):
        #
        # Resume processing a list content.  To do this, we
        # really need to simply push the 'list' content
        # back onto the resolver stack.
        #
        self.resolver.push(Frame(content.type))
        
    def end(self, parent, content):
        #
        # End processing the content.  Make sure the content
        # ending matches the top of the resolver stack since for
        # list processing we play games with the resolver stack.
        #
        log.debug('ending content:\n%s', content)
        current = self.resolver.top().type
        if current == content.type:
            self.resolver.pop()
        else:
            raise Exception, \
                'content (end) mismatch: top=(%s) cont=(%s)' % \
                (current, content)
    
    def node(self, content):
        #
        # Create an XML node and namespace qualify as defined
        # by the schema (elementFormDefault).
        #
        ns = content.type.namespace()
        if content.type.form_qualified:
            node = Element(content.tag, ns=ns)
            node.addPrefix(ns[0], ns[1])
        else:
            node = Element(content.tag)
        self.encode(node, content)
        log.debug('created - node:\n%s', node)
        return node
    
    def setnil(self, node, content):
        #
        # Set the 'node' nil only if the XSD type
        # specifies that it is permitted.
        #
        if content.type.nillable:
            node.setnil()
            
    def setdefault(self, node, content):
        #
        # Set the node to the default value specified
        # by the XSD type.
        #
        default = content.type.default
        if default is None:
            pass
        else:
            node.setText(default)
        return default
    
    def optional(self, content):
        if content.type.optional():
            return True
        for a in content.ancestry:
            if a.optional():
                return True
        return False
    
    def encode(self, node, content):
        # Add (soap) encoding information only if the resolved
        # type is derived by extension.  Further, the xsi:type values
        # is qualified by namespace only if the content (tag) and
        # referenced type are in different namespaces.
        if content.type.any():
            return
        if not content.real.extension():
            return
        if content.type.resolve() == content.real:
            return
        ns = None
        name = content.real.name
        if self.xstq:
            ns = content.real.namespace('ns1')
        Typer.manual(node, name, ns)
    
    def skip(self, content):
        """
        Get whether to skip this I{content}.
        Should be skipped when the content is optional
        and either the value=None or the value is an empty list.
        @param content: The content to skip.
        @type content: L{Object}
        @return: True if content is to be skipped.
        @rtype: bool
        """
        if self.optional(content):
            v = content.value
            if v is None:
                return True
            if isinstance(v, (list,tuple)) and len(v) == 0:
                return True
        return False
    
    def optional(self, content):
        if content.type.optional():
            return True
        for a in content.ancestry:
            if a.optional():
                return True
        return False
    
    def translate(self, content):
        """
        Translate using the XSD type information.
        Python I{dict} is translated to a suds object.  Most
        importantly, primative values are translated from python
        types to XML types using the XSD type.
        @param content: The content to translate.
        @type content: L{Object}
        @return: self
        @rtype: L{Typed}
        """
        v = content.value
        if v is None:
            return
        if isinstance(v, dict):
            cls = content.real.name
            content.value = Factory.object(cls, v)
            md = content.value.__metadata__
            md.sxtype = content.type
            return
        v = content.real.translate(v, False)
        content.value = v
        return self
        
    def sort(self, content):
        """
        Sort suds object attributes based on ordering defined
        in the XSD type information.
        @param content: The content to sort.
        @type content: L{Object}
        @return: self
        @rtype: L{Typed}
        """
        v = content.value
        if isinstance(v, Object):
            md = v.__metadata__
            md.ordering = self.ordering(content.real)
        return self

    def ordering(self, type):
        """
        Get the attribute ordering defined in the specified
        XSD type information.
        @param type: An XSD type object.
        @type type: SchemaObject
        @return: An ordered list of attribute names.
        @rtype: list
        """
        result = []
        for child, ancestry in type.resolve():
            name = child.name
            if child.name is None:
                continue
            if child.isattr():
                name = '_%s' % child.name
            result.append(name)
        return result


class Literal(Typed):
    """
    A I{literal} marshaller.
    This marshaller is semi-typed as needed to support both
    I{document/literal} and I{rpc/literal} soap message styles.
    """
    pass