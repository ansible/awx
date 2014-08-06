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
Properties classes.
"""

from logging import getLogger

log = getLogger(__name__)


class AutoLinker(object):
    """
    Base class, provides interface for I{automatic} link
    management between a L{Properties} object and the L{Properties}
    contained within I{values}.
    """
    def updated(self, properties, prev, next):
        """
        Notification that a values was updated and the linkage
        between the I{properties} contained with I{prev} need to
        be relinked to the L{Properties} contained within the
        I{next} value.
        """
        pass


class Link(object):
    """
    Property link object.
    @ivar endpoints: A tuple of the (2) endpoints of the link.
    @type endpoints: tuple(2)
    """
    def __init__(self, a, b):
        """
        @param a: Property (A) to link.
        @type a: L{Property}
        @param b: Property (B) to link.
        @type b: L{Property}
        """
        pA = Endpoint(self, a)
        pB = Endpoint(self, b)
        self.endpoints = (pA, pB)
        self.validate(a, b)
        a.links.append(pB)
        b.links.append(pA)
            
    def validate(self, pA, pB):
        """
        Validate that the two properties may be linked.
        @param pA: Endpoint (A) to link.
        @type pA: L{Endpoint}
        @param pB: Endpoint (B) to link.
        @type pB: L{Endpoint}
        @return: self
        @rtype: L{Link}
        """
        if pA in pB.links or \
           pB in pA.links:
            raise Exception, 'Already linked'
        dA = pA.domains()
        dB = pB.domains()
        for d in dA:
            if d in dB:
                raise Exception, 'Duplicate domain "%s" found' % d
        for d in dB:
            if d in dA:
                raise Exception, 'Duplicate domain "%s" found' % d
        kA = pA.keys()
        kB = pB.keys()
        for k in kA:
            if k in kB:
                raise Exception, 'Duplicate key %s found' % k
        for k in kB:
            if k in kA:
                raise Exception, 'Duplicate key %s found' % k
        return self
            
    def teardown(self):
        """
        Teardown the link.
        Removes endpoints from properties I{links} collection.
        @return: self
        @rtype: L{Link}
        """
        pA, pB = self.endpoints
        if pA in pB.links:
            pB.links.remove(pA)
        if pB in pA.links:
            pA.links.remove(pB)
        return self


class Endpoint(object):
    """
    Link endpoint (wrapper).
    @ivar link: The associated link.
    @type link: L{Link}
    @ivar target: The properties object.
    @type target: L{Property}
    """
    def __init__(self, link, target):
        self.link = link
        self.target = target
        
    def teardown(self):
        return self.link.teardown()

    def __eq__(self, rhs):
        return ( self.target == rhs )

    def __hash__(self):
        return hash(self.target)

    def __getattr__(self, name):
        return getattr(self.target, name)


class Definition:
    """
    Property definition.
    @ivar name: The property name.
    @type name: str
    @ivar classes: The (class) list of permitted values
    @type classes: tuple
    @ivar default: The default value.
    @ivar type: any
    """
    def __init__(self, name, classes, default, linker=AutoLinker()):
        """
        @param name: The property name.
        @type name: str
        @param classes: The (class) list of permitted values
        @type classes: tuple
        @param default: The default value.
        @type default: any
        """
        if not isinstance(classes, (list, tuple)):
            classes = (classes,)
        self.name = name
        self.classes = classes
        self.default = default
        self.linker = linker
        
    def nvl(self, value=None):
        """
        Convert the I{value} into the default when I{None}.
        @param value: The proposed value.
        @type value: any
        @return: The I{default} when I{value} is I{None}, else I{value}.
        @rtype: any
        """
        if value is None:
            return self.default
        else:
            return value
        
    def validate(self, value):
        """
        Validate the I{value} is of the correct class.
        @param value: The value to validate.
        @type value: any
        @raise AttributeError: When I{value} is invalid.
        """
        if value is None:
            return
        if len(self.classes) and \
            not isinstance(value, self.classes):
                msg = '"%s" must be: %s' % (self.name, self.classes)
                raise AttributeError,msg
                    
            
    def __repr__(self):
        return '%s: %s' % (self.name, str(self))
            
    def __str__(self):
        s = []
        if len(self.classes):
            s.append('classes=%s' % str(self.classes))
        else:
            s.append('classes=*')
        s.append("default=%s" % str(self.default))
        return ', '.join(s)


class Properties:
    """
    Represents basic application properties.
    Provides basic type validation, default values and
    link/synchronization behavior.
    @ivar domain: The domain name.
    @type domain: str
    @ivar definitions: A table of property definitions.
    @type definitions: {name: L{Definition}}
    @ivar links: A list of linked property objects used to create
        a network of properties.
    @type links: [L{Property},..]
    @ivar defined: A dict of property values.
    @type defined: dict 
    """
    def __init__(self, domain, definitions, kwargs):
        """
        @param domain: The property domain name.
        @type domain: str
        @param definitions: A table of property definitions.
        @type definitions: {name: L{Definition}}
        @param kwargs: A list of property name/values to set.
        @type kwargs: dict  
        """
        self.definitions = {}
        for d in definitions:
            self.definitions[d.name] = d
        self.domain = domain
        self.links = []
        self.defined = {}
        self.modified = set()
        self.prime()
        self.update(kwargs)
        
    def definition(self, name):
        """
        Get the definition for the property I{name}.
        @param name: The property I{name} to find the definition for.
        @type name: str
        @return: The property definition
        @rtype: L{Definition}
        @raise AttributeError: On not found.
        """
        d = self.definitions.get(name)
        if d is None:
            raise AttributeError(name)
        return d
    
    def update(self, other):
        """
        Update the property values as specified by keyword/value.
        @param other: An object to update from.
        @type other: (dict|L{Properties})
        @return: self
        @rtype: L{Properties}
        """
        if isinstance(other, Properties):
            other = other.defined
        for n,v in other.items():
            self.set(n, v)
        return self
    
    def notset(self, name):
        """
        Get whether a property has never been set by I{name}.
        @param name: A property name.
        @type name: str
        @return: True if never been set.
        @rtype: bool
        """
        self.provider(name).__notset(name)
            
    def set(self, name, value):
        """
        Set the I{value} of a property by I{name}.
        The value is validated against the definition and set
        to the default when I{value} is None.
        @param name: The property name.
        @type name: str
        @param value: The new property value.
        @type value: any
        @return: self
        @rtype: L{Properties}
        """
        self.provider(name).__set(name, value)
        return self
    
    def unset(self, name):
        """
        Unset a property by I{name}.
        @param name: A property name.
        @type name: str
        @return: self
        @rtype: L{Properties}
        """
        self.provider(name).__set(name, None)
        return self
            
    def get(self, name, *df):
        """
        Get the value of a property by I{name}.
        @param name: The property name.
        @type name: str
        @param df: An optional value to be returned when the value
            is not set
        @type df: [1].
        @return: The stored value, or I{df[0]} if not set.
        @rtype: any 
        """
        return self.provider(name).__get(name, *df)
    
    def link(self, other):
        """
        Link (associate) this object with anI{other} properties object 
        to create a network of properties.  Links are bidirectional.
        @param other: The object to link.
        @type other: L{Properties}
        @return: self
        @rtype: L{Properties}
        """
        Link(self, other)
        return self

    def unlink(self, *others):
        """
        Unlink (disassociate) the specified properties object.
        @param others: The list object to unlink.  Unspecified means unlink all.
        @type others: [L{Properties},..]
        @return: self
        @rtype: L{Properties}
        """
        if not len(others):
            others = self.links[:]
        for p in self.links[:]:
            if p in others:
                p.teardown()
        return self
    
    def provider(self, name, history=None):
        """
        Find the provider of the property by I{name}.
        @param name: The property name.
        @type name: str
        @param history: A history of nodes checked to prevent
            circular hunting.
        @type history: [L{Properties},..]
        @return: The provider when found.  Otherwise, None (when nested)
            and I{self} when not nested.
        @rtype: L{Properties}
        """
        if history is None:
            history = []
        history.append(self)
        if name in self.definitions:
            return self
        for x in self.links:
            if x in history:
                continue
            provider = x.provider(name, history)
            if provider is not None:
                return provider
        history.remove(self)
        if len(history):
            return None
        return self
    
    def keys(self, history=None):
        """
        Get the set of I{all} property names.
        @param history: A history of nodes checked to prevent
            circular hunting.
        @type history: [L{Properties},..]
        @return: A set of property names.
        @rtype: list
        """
        if history is None:
            history = []
        history.append(self)
        keys = set()
        keys.update(self.definitions.keys())
        for x in self.links:
            if x in history:
                continue
            keys.update(x.keys(history))
        history.remove(self)
        return keys
    
    def domains(self, history=None):
        """
        Get the set of I{all} domain names.
        @param history: A history of nodes checked to prevent
            circular hunting.
        @type history: [L{Properties},..]
        @return: A set of domain names.
        @rtype: list
        """
        if history is None:
            history = []
        history.append(self)
        domains = set()
        domains.add(self.domain)
        for x in self.links:
            if x in history:
                continue
            domains.update(x.domains(history))
        history.remove(self)
        return domains
 
    def prime(self):
        """
        Prime the stored values based on default values
        found in property definitions.
        @return: self
        @rtype: L{Properties}
        """
        for d in self.definitions.values():
            self.defined[d.name] = d.default
        return self
    
    def __notset(self, name):
        return not (name in self.modified)
    
    def __set(self, name, value):
        d = self.definition(name)
        d.validate(value)
        value = d.nvl(value)
        prev = self.defined[name]
        self.defined[name] = value
        self.modified.add(name)
        d.linker.updated(self, prev, value)
        
    def __get(self, name, *df):
        d = self.definition(name)
        value = self.defined.get(name)
        if value == d.default and len(df):
            value = df[0]
        return value
            
    def str(self, history):
        s = []
        s.append('Definitions:')
        for d in self.definitions.values():
            s.append('\t%s' % repr(d))
        s.append('Content:')
        for d in self.defined.items():
            s.append('\t%s' % str(d))
        if self not in history:
            history.append(self)
            s.append('Linked:')
            for x in self.links:
                s.append(x.str(history))
            history.remove(self)
        return '\n'.join(s)
            
    def __repr__(self):
        return str(self)
            
    def __str__(self):
        return self.str([])


class Skin(object):
    """
    The meta-programming I{skin} around the L{Properties} object.
    @ivar __pts__: The wrapped object.
    @type __pts__: L{Properties}.
    """
    def __init__(self, domain, definitions, kwargs):
        self.__pts__ = Properties(domain, definitions, kwargs)
        
    def __setattr__(self, name, value):
        builtin = name.startswith('__') and name.endswith('__')
        if builtin:
            self.__dict__[name] = value
            return
        self.__pts__.set(name, value)
        
    def __getattr__(self, name):
        return self.__pts__.get(name)
    
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        return str(self.__pts__)
    
    
class Unskin(object):
    def __new__(self, *args, **kwargs):
        return args[0].__pts__
    
    
class Inspector:
    """
    Wrapper inspector.
    """
    def __init__(self, options):
        self.properties = options.__pts__
        
    def get(self, name, *df):
        """
        Get the value of a property by I{name}.
        @param name: The property name.
        @type name: str
        @param df: An optional value to be returned when the value
            is not set
        @type df: [1].
        @return: The stored value, or I{df[0]} if not set.
        @rtype: any 
        """
        return self.properties.get(name, *df)

    def update(self, **kwargs):
        """
        Update the property values as specified by keyword/value.
        @param kwargs: A list of property name/values to set.
        @type kwargs: dict
        @return: self
        @rtype: L{Properties}
        """
        return self.properties.update(**kwargs)

    def link(self, other):
        """
        Link (associate) this object with anI{other} properties object 
        to create a network of properties.  Links are bidirectional.
        @param other: The object to link.
        @type other: L{Properties}
        @return: self
        @rtype: L{Properties}
        """
        p = other.__pts__
        return self.properties.link(p)
    
    def unlink(self, other):
        """
        Unlink (disassociate) the specified properties object.
        @param other: The object to unlink.
        @type other: L{Properties}
        @return: self
        @rtype: L{Properties}
        """
        p = other.__pts__
        return self.properties.unlink(p)
