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
The I{sxbase} module provides I{base} classes that represent
schema objects.
"""

from logging import getLogger
from suds import *
from suds.xsd import *
from suds.sax.element import Element
from suds.sax import Namespace

log = getLogger(__name__)


class SchemaObject(object):
    """
    A schema object is an extension to object object with
    with schema awareness.
    @ivar root: The XML root element.
    @type root: L{Element}
    @ivar schema: The schema containing this object.
    @type schema: L{schema.Schema}
    @ivar form_qualified: A flag that inidcates that @elementFormDefault
        has a value of I{qualified}.
    @type form_qualified: boolean
    @ivar nillable: A flag that inidcates that @nillable
        has a value of I{true}.
    @type nillable: boolean
    @ivar default: The default value.
    @type default: object
    @ivar rawchildren: A list raw of all children.
    @type rawchildren: [L{SchemaObject},...]
    """

    @classmethod
    def prepend(cls, d, s, filter=Filter()):
        """
        Prepend schema object's from B{s}ource list to 
        the B{d}estination list while applying the filter.
        @param d: The destination list.
        @type d: list
        @param s: The source list.
        @type s: list
        @param filter: A filter that allows items to be prepended.
        @type filter: L{Filter}
        """
        i = 0
        for x in s:
            if x in filter:
                d.insert(i, x)
                i += 1
    
    @classmethod
    def append(cls, d, s, filter=Filter()):
        """
        Append schema object's from B{s}ource list to 
        the B{d}estination list while applying the filter.
        @param d: The destination list.
        @type d: list
        @param s: The source list.
        @type s: list
        @param filter: A filter that allows items to be appended.
        @type filter: L{Filter}
        """
        for item in s:
            if item in filter:
                d.append(item)

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{Element}
        """
        self.schema = schema
        self.root = root
        self.id = objid(self)
        self.name = root.get('name')
        self.qname = (self.name, schema.tns[1])
        self.min = root.get('minOccurs')
        self.max = root.get('maxOccurs')
        self.type = root.get('type')
        self.ref = root.get('ref')
        self.form_qualified = schema.form_qualified
        self.nillable = False
        self.default = root.get('default')
        self.rawchildren = []
        self.cache = {}
        
    def attributes(self, filter=Filter()):
        """
        Get only the attribute content.
        @param filter: A filter to constrain the result.
        @type filter: L{Filter}
        @return: A list of tuples (attr, ancestry)
        @rtype: [(L{SchemaObject}, [L{SchemaObject},..]),..]
        """
        result = []
        for child, ancestry in self:
            if child.isattr() and child in filter:
                result.append((child, ancestry))
        return result
                
    def children(self, filter=Filter()):
        """
        Get only the I{direct} or non-attribute content.
        @param filter: A filter to constrain the result.
        @type filter: L{Filter}
        @return: A list tuples: (child, ancestry)
        @rtype: [(L{SchemaObject}, [L{SchemaObject},..]),..]
        """
        result = []
        for child, ancestry in self:
            if not child.isattr() and child in filter:
                result.append((child, ancestry))
        return result
                
    def get_attribute(self, name):
        """
        Get (find) a I{non-attribute} attribute by name.
        @param name: A attribute name.
        @type name: str
        @return: A tuple: the requested (attribute, ancestry).
        @rtype: (L{SchemaObject}, [L{SchemaObject},..])
        """
        for child, ancestry in self.attributes():
            if child.name == name:
                return (child, ancestry)
        return (None, [])
                
    def get_child(self, name):
        """
        Get (find) a I{non-attribute} child by name.
        @param name: A child name.
        @type name: str
        @return: A tuple: the requested (child, ancestry).
        @rtype: (L{SchemaObject}, [L{SchemaObject},..])
        """
        for child, ancestry in self.children():
            if child.any() or child.name == name:
                return (child, ancestry)
        return (None, [])

    def namespace(self, prefix=None):
        """
        Get this properties namespace
        @param prefix: The default prefix.
        @type prefix: str
        @return: The schema's target namespace
        @rtype: (I{prefix},I{URI})
        """
        ns = self.schema.tns
        if ns[0] is None:
            ns = (prefix, ns[1])
        return ns
    
    def default_namespace(self):
        return self.root.defaultNamespace()
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        max = self.max
        if max is None:
            max = '1'
        if max.isdigit():
            return (int(max) > 1)
        else:
            return ( max == 'unbounded' )
    
    def optional(self):
        """
        Get whether this type is optional.
        @return: True if optional, else False
        @rtype: boolean
        """
        min = self.min
        if min is None:
            min = '1'
        return ( min == '0' )
    
    def required(self):
        """
        Get whether this type is required.
        @return: True if required, else False
        @rtype: boolean
        """
        return ( not self.optional() )
        
    
    def resolve(self, nobuiltin=False):
        """
        Resolve and return the nodes true self.
        @param nobuiltin: Flag indicates that resolution must
            not continue to include xsd builtins.
        @return: The resolved (true) type.
        @rtype: L{SchemaObject}
        """
        return self.cache.get(nobuiltin, self)
    
    def sequence(self):
        """
        Get whether this is an <xs:sequence/>
        @return: True if <xs:sequence/>, else False
        @rtype: boolean
        """
        return False
    
    def xslist(self):
        """
        Get whether this is an <xs:list/>
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def all(self):
        """
        Get whether this is an <xs:all/>
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def choice(self):
        """
        Get whether this is n <xs:choice/>
        @return: True if any, else False
        @rtype: boolean
        """
        return False
        
    def any(self):
        """
        Get whether this is an <xs:any/>
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def builtin(self):
        """
        Get whether this is a schema-instance (xs) type.
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def enum(self):
        """
        Get whether this is a simple-type containing an enumeration.
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def isattr(self):
        """
        Get whether the object is a schema I{attribute} definition.
        @return: True if an attribute, else False.
        @rtype: boolean
        """
        return False
    
    def extension(self):
        """
        Get whether the object is an extension of another type.
        @return: True if an extension, else False.
        @rtype: boolean
        """
        return False
    
    def restriction(self):
        """
        Get whether the object is an restriction of another type.
        @return: True if an restriction, else False.
        @rtype: boolean
        """
        return False
    
    def mixed(self):
        """
        Get whether this I{mixed} content.
        """
        return False
        
    def find(self, qref, classes=()):
        """
        Find a referenced type in self or children.
        @param qref: A qualified reference.
        @type qref: qref
        @param classes: A list of classes used to qualify the match.
        @type classes: [I{class},...] 
        @return: The referenced type.
        @rtype: L{SchemaObject}
        @see: L{qualify()}
        """
        if not len(classes):
            classes = (self.__class__,)
        if self.qname == qref and self.__class__ in classes:
            return self
        for c in self.rawchildren:
            p = c.find(qref, classes)
            if p is not None:
                return p
        return None

    def translate(self, value, topython=True):
        """
        Translate a value (type) to/from a python type.
        @param value: A value to translate.
        @return: The converted I{language} type.
        """
        return value
    
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ()
    
    def dependencies(self):
        """
        Get a list of dependancies for dereferencing.
        @return: A merge dependancy index and a list of dependancies.
        @rtype: (int, [L{SchemaObject},...])
        """
        return (None, [])
    
    def autoqualified(self):
        """
        The list of I{auto} qualified attribute values.
        Qualification means to convert values into I{qref}.
        @return: A list of attibute names.
        @rtype: list
        """
        return ['type', 'ref']
    
    def qualify(self):
        """
        Convert attribute values, that are references to other
        objects, into I{qref}.  Qualfied using default document namespace.
        Since many wsdls are written improperly: when the document does
        not define a default namespace, the schema target namespace is used
        to qualify references.
        """
        defns = self.root.defaultNamespace()
        if Namespace.none(defns):
            defns = self.schema.tns
        for a in self.autoqualified():
            ref = getattr(self, a)
            if ref is None:
                continue
            if isqref(ref):
                continue
            qref = qualify(ref, self.root, defns)
            log.debug('%s, convert %s="%s" to %s', self.id, a, ref, qref)
            setattr(self, a, qref)
            
    def merge(self, other):
        """
        Merge another object as needed.
        """
        other.qualify()
        for n in ('name',
                  'qname',
                  'min',
                  'max',
                  'default',
                  'type',
                  'nillable',
                  'form_qualified',):
            if getattr(self, n) is not None:
                continue
            v = getattr(other, n)
            if v is None:
                continue
            setattr(self, n, v)
            
            
    def content(self, collection=None, filter=Filter(), history=None):
        """
        Get a I{flattened} list of this nodes contents.
        @param collection: A list to fill.
        @type collection: list
        @param filter: A filter used to constrain the result.
        @type filter: L{Filter}
        @param history: The history list used to prevent cyclic dependency.
        @type history: list
        @return: The filled list.
        @rtype: list
        """
        if collection is None:
            collection = []
        if history is None:
            history = []
        if self in history:
            return collection
        history.append(self)
        if self in filter:
            collection.append(self)
        for c in self.rawchildren:
            c.content(collection, filter, history[:])
        return collection
    
    def str(self, indent=0, history=None):
        """
        Get a string representation of this object.
        @param indent: The indent.
        @type indent: int
        @return: A string.
        @rtype: str
        """
        if history is None: 
            history = []
        if self in history:
            return '%s ...' % Repr(self)
        history.append(self)
        tab = '%*s'%(indent*3, '')
        result  = []
        result.append('%s<%s' % (tab, self.id))
        for n in self.description():
            if not hasattr(self, n):
                continue
            v = getattr(self, n)
            if v is None:
                continue
            result.append(' %s="%s"' % (n, v))
        if len(self):
            result.append('>')
            for c in self.rawchildren:
                result.append('\n')
                result.append(c.str(indent+1, history[:]))
                if c.isattr():
                    result.append('@')
            result.append('\n%s' % tab)
            result.append('</%s>' % self.__class__.__name__)
        else:
            result.append(' />')
        return ''.join(result)
    
    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ()
        
    def __str__(self):
        return unicode(self).encode('utf-8')
            
    def __unicode__(self):
        return unicode(self.str())
    
    def __repr__(self):
        s = []
        s.append('<%s' % self.id)
        for n in self.description():
            if not hasattr(self, n):
                continue
            v = getattr(self, n)
            if v is None:
                continue
            s.append(' %s="%s"' % (n, v))
        s.append(' />')
        myrep = ''.join(s)
        return myrep.encode('utf-8')
    
    def __len__(self):
        n = 0
        for x in self: n += 1
        return n
    
    def __iter__(self):
        return Iter(self)
    
    def __getitem__(self, index):
        i = 0
        for c in self:
            if i == index:
                return c


class Iter:
    """
    The content iterator - used to iterate the L{Content} children.  The iterator
    provides a I{view} of the children that is free of container elements
    such as <sequence/> and <choice/>.
    @ivar stack: A stack used to control nesting.
    @type stack: list
    """
    
    class Frame:
        """ A content iterator frame. """
        
        def __init__(self, sx):
            """
            @param sx: A schema object.
            @type sx: L{SchemaObject}
            """
            self.sx = sx
            self.items = sx.rawchildren
            self.index = 0
            
        def next(self):
            """
            Get the I{next} item in the frame's collection.
            @return: The next item or None
            @rtype: L{SchemaObject}
            """
            if self.index < len(self.items):
                result = self.items[self.index]
                self.index += 1
                return result
    
    def __init__(self, sx):
        """
        @param sx: A schema object.
        @type sx: L{SchemaObject}
        """
        self.stack = []
        self.push(sx)
        
    def push(self, sx):
        """
        Create a frame and push the specified object.
        @param sx: A schema object to push.
        @type sx: L{SchemaObject}
        """
        self.stack.append(Iter.Frame(sx))
        
    def pop(self):
        """
        Pop the I{top} frame.
        @return: The popped frame.
        @rtype: L{Frame}
        @raise StopIteration: when stack is empty.
        """
        if len(self.stack):
            return self.stack.pop()
        else:
            raise StopIteration()
        
    def top(self):
        """
        Get the I{top} frame.
        @return: The top frame.
        @rtype: L{Frame}
        @raise StopIteration: when stack is empty.
        """
        if len(self.stack):
            return self.stack[-1]
        else:
            raise StopIteration()
    
    def next(self):
        """
        Get the next item.
        @return: A tuple: the next (child, ancestry).
        @rtype: (L{SchemaObject}, [L{SchemaObject},..])
        @raise StopIteration: A the end.
        """
        frame = self.top()
        while True:
            result = frame.next()
            if result is None:
                self.pop()
                return self.next()
            if isinstance(result, Content):
                ancestry = [f.sx for f in self.stack]
                return (result, ancestry)
            self.push(result)
            return self.next()
    
    def __iter__(self):
        return self


class XBuiltin(SchemaObject):
    """
    Represents an (xsd) schema <xs:*/> node
    """
    
    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        """
        root = Element(name)
        SchemaObject.__init__(self, schema, root)
        self.name = name
        self.nillable = True
            
    def namespace(self, prefix=None):
        return Namespace.xsdns
    
    def builtin(self):
        return True
    
    def resolve(self, nobuiltin=False):
        return self


class Content(SchemaObject):
    """
    This class represents those schema objects that represent
    real XML document content.
    """
    pass

    
class NodeFinder:
    """
    Find nodes based on flexable criteria.  The I{matcher} is
    may be any object that implements a match(n) method.
    @ivar matcher: An object used as criteria for match.
    @type matcher: I{any}.match(n)
    @ivar limit: Limit the number of matches.  0=unlimited.
    @type limit: int
    """
    def __init__(self, matcher, limit=0):
        """
        @param matcher: An object used as criteria for match.
        @type matcher: I{any}.match(n)
        @param limit: Limit the number of matches.  0=unlimited.
        @type limit: int
        """
        self.matcher = matcher
        self.limit = limit
        
    def find(self, node, list):
        """
        Traverse the tree looking for matches.
        @param node: A node to match on.
        @type node: L{SchemaObject}
        @param list: A list to fill.
        @type list: list
        """
        if self.matcher.match(node):
            list.append(node)
            self.limit -= 1
            if self.limit == 0:
                return
        for c in node.rawchildren:
            self.find(c, list)
        return self