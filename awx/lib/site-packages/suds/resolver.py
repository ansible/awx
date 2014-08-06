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
The I{resolver} module provides a collection of classes that
provide wsdl/xsd named type resolution.
"""

import re
from logging import getLogger
from suds import *
from suds.sax import splitPrefix, Namespace
from suds.sudsobject import Object
from suds.xsd.query import BlindQuery, TypeQuery, qualify

log = getLogger(__name__)


class Resolver:
    """
    An I{abstract} schema-type resolver.
    @ivar schema: A schema object.
    @type schema: L{xsd.schema.Schema}
    """

    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{xsd.schema.Schema}
        """
        self.schema = schema
        
    def find(self, name, resolved=True):
        """
        Get the definition object for the schema object by name.
        @param name: The name of a schema object.
        @type name: basestring
        @param resolved: A flag indicating that the fully resolved type
            should be returned.
        @type resolved: boolean
        @return: The found schema I{type}
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        log.debug('searching schema for (%s)', name)
        qref = qualify(name, self.schema.root, self.schema.tns)
        query = BlindQuery(qref)
        result = query.execute(self.schema)
        if result is None:
            log.error('(%s) not-found', name)
            return None
        log.debug('found (%s) as (%s)', name, Repr(result))
        if resolved:
            result = result.resolve()
        return result


class PathResolver(Resolver):
    """
    Resolveds the definition object for the schema type located at the specified path.
    The path may contain (.) dot notation to specify nested types.
    @ivar wsdl: A wsdl object.
    @type wsdl: L{wsdl.Definitions}
    """

    def __init__(self, wsdl, ps='.'):
        """
        @param wsdl: A schema object.
        @type wsdl: L{wsdl.Definitions}
        @param ps: The path separator character
        @type ps: char
        """
        Resolver.__init__(self, wsdl.schema)
        self.wsdl = wsdl
        self.altp = re.compile('({)(.+)(})(.+)')
        self.splitp = re.compile('({.+})*[^\%s]+' % ps[0])

    def find(self, path, resolved=True):
        """
        Get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        Actually, the path separator is usually a (.) but can be redefined
        during contruction.
        @param path: A (.) separated path to a schema type.
        @type path: basestring
        @param resolved: A flag indicating that the fully resolved type
            should be returned.
        @type resolved: boolean
        @return: The found schema I{type}
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        result = None
        parts = self.split(path)
        try:
            result = self.root(parts)
            if len(parts) > 1:
                result = result.resolve(nobuiltin=True)
                result = self.branch(result, parts)
                result = self.leaf(result, parts)
            if resolved:
                result = result.resolve(nobuiltin=True)
        except PathResolver.BadPath:
            log.error('path: "%s", not-found' % path)
        return result
    
    def root(self, parts):
        """
        Find the path root.
        @param parts: A list of path parts.
        @type parts: [str,..]
        @return: The root.
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        result = None
        name = parts[0]
        log.debug('searching schema for (%s)', name)
        qref = self.qualify(parts[0])
        query = BlindQuery(qref)
        result = query.execute(self.schema)
        if result is None:
            log.error('(%s) not-found', name)
            raise PathResolver.BadPath(name)
        else:
            log.debug('found (%s) as (%s)', name, Repr(result))
        return result
    
    def branch(self, root, parts):
        """
        Traverse the path until the leaf is reached.
        @param parts: A list of path parts.
        @type parts: [str,..]
        @param root: The root.
        @type root: L{xsd.sxbase.SchemaObject}
        @return: The end of the branch.
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        result = root
        for part in parts[1:-1]:
            name = splitPrefix(part)[1]
            log.debug('searching parent (%s) for (%s)', Repr(result), name)
            result, ancestry = result.get_child(name)
            if result is None:
                log.error('(%s) not-found', name)
                raise PathResolver.BadPath(name)
            else:
                result = result.resolve(nobuiltin=True)
                log.debug('found (%s) as (%s)', name, Repr(result))
        return result
    
    def leaf(self, parent, parts):
        """
        Find the leaf.
        @param parts: A list of path parts.
        @type parts: [str,..]
        @param parent: The leaf's parent.
        @type parent: L{xsd.sxbase.SchemaObject}
        @return: The leaf.
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        name = splitPrefix(parts[-1])[1]
        if name.startswith('@'):
            result, path = parent.get_attribute(name[1:])
        else:
            result, ancestry = parent.get_child(name)
        if result is None:
            raise PathResolver.BadPath(name)
        return result
    
    def qualify(self, name):
        """
        Qualify the name as either:
          - plain name
          - ns prefixed name (eg: ns0:Person)
          - fully ns qualified name (eg: {http://myns-uri}Person)
        @param name: The name of an object in the schema.
        @type name: str
        @return: A qualifed name.
        @rtype: qname
        """
        m = self.altp.match(name)
        if m is None:
            return qualify(name, self.wsdl.root, self.wsdl.tns)
        else:
            return (m.group(4), m.group(2))
        
    def split(self, s):
        """
        Split the string on (.) while preserving any (.) inside the
        '{}' alternalte syntax for full ns qualification.
        @param s: A plain or qualifed name.
        @type s: str
        @return: A list of the name's parts.
        @rtype: [str,..]
        """
        parts = []
        b = 0
        while 1:
            m = self.splitp.match(s, b)
            if m is None:
                break
            b,e = m.span()
            parts.append(s[b:e])
            b = e+1
        return parts
    
    class BadPath(Exception): pass


class TreeResolver(Resolver):
    """
    The tree resolver is a I{stateful} tree resolver
    used to resolve each node in a tree.  As such, it mirrors
    the tree structure to ensure that nodes are resolved in
    context.
    @ivar stack: The context stack.
    @type stack: list
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{xsd.schema.Schema}
        """
        Resolver.__init__(self, schema)
        self.stack = Stack()
        
    def reset(self):
        """
        Reset the resolver's state.
        """
        self.stack = Stack()
            
    def push(self, x):
        """
        Push an I{object} onto the stack.
        @param x: An object to push.
        @type x: L{Frame}
        @return: The pushed frame.
        @rtype: L{Frame}
        """
        if isinstance(x, Frame):
            frame = x
        else:
            frame = Frame(x)
        self.stack.append(frame)
        log.debug('push: (%s)\n%s', Repr(frame), Repr(self.stack))
        return frame
    
    def top(self):
        """
        Get the I{frame} at the top of the stack.
        @return: The top I{frame}, else None.
        @rtype: L{Frame}
        """
        if len(self.stack):
            return self.stack[-1]
        else:
            return Frame.Empty()
        
    def pop(self):
        """
        Pop the frame at the top of the stack.
        @return: The popped frame, else None.
        @rtype: L{Frame}
        """
        if len(self.stack):      
            popped = self.stack.pop()
            log.debug('pop: (%s)\n%s', Repr(popped), Repr(self.stack))
            return popped
        else:
            log.debug('stack empty, not-popped')
        return None
    
    def depth(self):
        """
        Get the current stack depth.
        @return: The current stack depth.
        @rtype: int
        """
        return len(self.stack)
    
    def getchild(self, name, parent):
        """ get a child by name """
        log.debug('searching parent (%s) for (%s)', Repr(parent), name)
        if name.startswith('@'):
            return parent.get_attribute(name[1:])
        else:
            return parent.get_child(name)


class NodeResolver(TreeResolver):
    """
    The node resolver is a I{stateful} XML document resolver
    used to resolve each node in a tree.  As such, it mirrors
    the tree structure to ensure that nodes are resolved in
    context.
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{xsd.schema.Schema}
        """
        TreeResolver.__init__(self, schema)
        
    def find(self, node, resolved=False, push=True):
        """
        @param node: An xml node to be resolved.
        @type node: L{sax.element.Element}
        @param resolved: A flag indicating that the fully resolved type should be
            returned.
        @type resolved: boolean
        @param push: Indicates that the resolved type should be
            pushed onto the stack.
        @type push: boolean
        @return: The found schema I{type}
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        name = node.name
        parent = self.top().resolved
        if parent is None:
            result, ancestry = self.query(name, node)
        else:
            result, ancestry = self.getchild(name, parent)
        known = self.known(node)
        if result is None:
            return result
        if push:
            frame = Frame(result, resolved=known, ancestry=ancestry)
            pushed = self.push(frame)
        if resolved:
            result = result.resolve()
        return result
    
    def findattr(self, name, resolved=True):
        """
        Find an attribute type definition.
        @param name: An attribute name.
        @type name: basestring
        @param resolved: A flag indicating that the fully resolved type should be
            returned.
        @type resolved: boolean
        @return: The found schema I{type}
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        name = '@%s'%name
        parent = self.top().resolved
        if parent is None:
            result, ancestry = self.query(name, node)
        else:
            result, ancestry = self.getchild(name, parent)
        if result is None:
            return result
        if resolved:
            result = result.resolve()
        return result
    
    def query(self, name, node):
        """ blindly query the schema by name """
        log.debug('searching schema for (%s)', name)
        qref = qualify(name, node, node.namespace())
        query = BlindQuery(qref)
        result = query.execute(self.schema)
        return (result, [])
    
    def known(self, node):
        """ resolve type referenced by @xsi:type """
        ref = node.get('type', Namespace.xsins)
        if ref is None:
            return None
        qref = qualify(ref, node, node.namespace())
        query = BlindQuery(qref)
        return query.execute(self.schema)
        

class GraphResolver(TreeResolver):
    """
    The graph resolver is a I{stateful} L{Object} graph resolver
    used to resolve each node in a tree.  As such, it mirrors
    the tree structure to ensure that nodes are resolved in
    context.
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{xsd.schema.Schema}
        """
        TreeResolver.__init__(self, schema)
        
    def find(self, name, object, resolved=False, push=True):
        """
        @param name: The name of the object to be resolved.
        @type name: basestring
        @param object: The name's value.
        @type object: (any|L{Object}) 
        @param resolved: A flag indicating that the fully resolved type
            should be returned.
        @type resolved: boolean
        @param push: Indicates that the resolved type should be
            pushed onto the stack.
        @type push: boolean
        @return: The found schema I{type}
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        known = None
        parent = self.top().resolved
        if parent is None:
            result, ancestry = self.query(name)
        else:
            result, ancestry = self.getchild(name, parent)
        if result is None:
            return None
        if isinstance(object, Object):
            known = self.known(object)
        if push:
            frame = Frame(result, resolved=known, ancestry=ancestry)
            pushed = self.push(frame)
        if resolved:
            if known is None:
                result = result.resolve()
            else:
                result = known
        return result
    
    def query(self, name):
        """ blindly query the schema by name """
        log.debug('searching schema for (%s)', name)
        schema = self.schema
        wsdl = self.wsdl()
        if wsdl is None:
            qref = qualify(name, schema.root, schema.tns)
        else:
            qref = qualify(name, wsdl.root, wsdl.tns)
        query = BlindQuery(qref)
        result = query.execute(schema)
        return (result, [])
    
    def wsdl(self):
        """ get the wsdl """
        container = self.schema.container
        if container is None:
            return None
        else:
            return container.wsdl
    
    def known(self, object):
        """ get the type specified in the object's metadata """
        try:
            md = object.__metadata__
            known = md.sxtype
            return known
        except:
            pass

       
class Frame:
    def __init__(self, type, resolved=None, ancestry=()):
        self.type = type
        if resolved is None:
            resolved = type.resolve()
        self.resolved = resolved.resolve()
        self.ancestry = ancestry

    def __str__(self):
        return '%s\n%s\n%s' % \
            (Repr(self.type),
            Repr(self.resolved),
            [Repr(t) for t in self.ancestry])
            
    class Empty:
        def __getattr__(self, name):
            if name == 'ancestry':
                return ()
            else:
                return None


class Stack(list):
    def __repr__(self):
        result = []
        for item in self:
            result.append(repr(item))
        return '\n'.join(result)