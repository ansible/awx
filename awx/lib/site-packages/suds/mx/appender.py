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
Provides appender classes for I{marshalling}.
"""

from logging import getLogger
from suds import *
from suds.mx import *
from suds.sudsobject import footprint
from suds.sudsobject import Object, Property
from suds.sax.element import Element
from suds.sax.text import Text
from copy import deepcopy

log = getLogger(__name__)

class Matcher:
    """
    Appender matcher.
    @ivar cls: A class object.
    @type cls: I{classobj}
    """

    def __init__(self, cls):
        """
        @param cls: A class object.
        @type cls: I{classobj}
        """
        self.cls = cls

    def __eq__(self, x):
        if self.cls is None:
            return ( x is None )
        else:
            return isinstance(x, self.cls)


class ContentAppender:
    """
    Appender used to add content to marshalled objects.
    @ivar default: The default appender.
    @type default: L{Appender}
    @ivar appenders: A I{table} of appenders mapped by class.
    @type appenders: I{table}
    """

    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{suds.mx.core.Core}
        """
        self.default = PrimativeAppender(marshaller)
        self.appenders = (
            (Matcher(None),
                NoneAppender(marshaller)),
            (Matcher(null),
                NoneAppender(marshaller)),
            (Matcher(Property),
                PropertyAppender(marshaller)),
            (Matcher(Object),
                ObjectAppender(marshaller)),
            (Matcher(Element), 
                ElementAppender(marshaller)),
            (Matcher(Text), 
                TextAppender(marshaller)),
            (Matcher(list), 
                ListAppender(marshaller)),
            (Matcher(tuple), 
                ListAppender(marshaller)),
            (Matcher(dict), 
                DictAppender(marshaller)),
        )
        
    def append(self, parent, content):
        """
        Select an appender and append the content to parent.
        @param parent: A parent node.
        @type parent: L{Element}
        @param content: The content to append.
        @type content: L{Content}
        """
        appender = self.default
        for a in self.appenders:
            if a[0] == content.value:
                appender = a[1]
                break
        appender.append(parent, content)


class Appender:
    """
    An appender used by the marshaller to append content.
    @ivar marshaller: A marshaller.
    @type marshaller: L{suds.mx.core.Core}
    """
    
    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{suds.mx.core.Core}
        """
        self.marshaller  = marshaller
        
    def node(self, content):
        """
        Create and return an XML node that is qualified
        using the I{type}.  Also, make sure all referenced namespace
        prefixes are declared.
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        @return: A new node.
        @rtype: L{Element}
        """
        return self.marshaller.node(content)
    
    def setnil(self, node, content):
        """
        Set the value of the I{node} to nill.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        self.marshaller.setnil(node, content)
        
    def setdefault(self, node, content):
        """
        Set the value of the I{node} to a default value.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        @return: The default.
        """
        return self.marshaller.setdefault(node, content)
    
    def optional(self, content):
        """
        Get whether the specified content is optional.
        @param content: The content which to check.
        @type content: L{Content}
        """
        return self.marshaller.optional(content)
        
    def suspend(self, content):
        """
        Notify I{marshaller} that appending this content has suspended.
        @param content: The content for which proccessing has been suspended.
        @type content: L{Object}
        """
        self.marshaller.suspend(content)
        
    def resume(self, content):
        """
        Notify I{marshaller} that appending this content has resumed.
        @param content: The content for which proccessing has been resumed.
        @type content: L{Object}
        """
        self.marshaller.resume(content)
    
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        self.marshaller.append(parent, content)

       
class PrimativeAppender(Appender):
    """
    An appender for python I{primative} types.
    """
        
    def append(self, parent, content):
        if content.tag.startswith('_'):
            attr = content.tag[1:]
            value = tostr(content.value)
            if value:
                parent.set(attr, value)
        else:
            child = self.node(content)
            child.setText(tostr(content.value))
            parent.append(child)


class NoneAppender(Appender):
    """
    An appender for I{None} values.
    """
        
    def append(self, parent, content):
        child = self.node(content)
        default = self.setdefault(child, content)
        if default is None:
            self.setnil(child, content)
        parent.append(child)


class PropertyAppender(Appender):
    """
    A L{Property} appender.
    """
        
    def append(self, parent, content):
        p = content.value
        child = self.node(content)
        child.setText(p.get())
        parent.append(child)
        for item in p.items():
            cont = Content(tag=item[0], value=item[1])
            Appender.append(self, child, cont)

            
class ObjectAppender(Appender):
    """
    An L{Object} appender.
    """
        
    def append(self, parent, content):
        object = content.value
        if self.optional(content) and footprint(object) == 0:
            return
        child = self.node(content)
        parent.append(child)
        for item in object:
            cont = Content(tag=item[0], value=item[1])
            Appender.append(self, child, cont)
            

class DictAppender(Appender):
    """
    An python I{dict} appender.
    """
        
    def append(self, parent, content):
        d = content.value
        if self.optional(content) and len(d) == 0:
            return
        child = self.node(content)
        parent.append(child)
        for item in d.items():
            cont = Content(tag=item[0], value=item[1])
            Appender.append(self, child, cont)
            

class ElementWrapper(Element):
    """
    Element wrapper.
    """
    
    def __init__(self, content):
        Element.__init__(self, content.name, content.parent)
        self.__content = content
        
    def str(self, indent=0):
        return self.__content.str(indent)


class ElementAppender(Appender):
    """
    An appender for I{Element} types.
    """

    def append(self, parent, content):
        if content.tag.startswith('_'):
            raise Exception('raw XML not valid as attribute value')
        child = ElementWrapper(content.value)
        parent.append(child)


class ListAppender(Appender):
    """
    A list/tuple appender.
    """

    def append(self, parent, content):
        collection = content.value
        if len(collection):
            self.suspend(content)
            for item in collection:
                cont = Content(tag=content.tag, value=item)
                Appender.append(self, parent, cont)
            self.resume(content)


class TextAppender(Appender):
    """
    An appender for I{Text} values.
    """

    def append(self, parent, content):
        if content.tag.startswith('_'):
            attr = content.tag[1:]
            value = tostr(content.value)
            if value:
                parent.set(attr, value)
        else:
            child = self.node(content)
            child.setText(content.value)
            parent.append(child)
