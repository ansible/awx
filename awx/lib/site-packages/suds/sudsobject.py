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
The I{sudsobject} module provides a collection of suds objects
that are primarily used for the highly dynamic interactions with
wsdl/xsd defined types.
"""

from logging import getLogger
from suds import *
from new import classobj

log = getLogger(__name__)


def items(sobject):
    """
    Extract the I{items} from a suds object much like the
    items() method works on I{dict}.
    @param sobject: A suds object
    @type sobject: L{Object}
    @return: A list of items contained in I{sobject}.
    @rtype: [(key, value),...]
    """
    for item in sobject:
        yield item


def asdict(sobject):
    """
    Convert a sudsobject into a dictionary.
    @param sobject: A suds object
    @type sobject: L{Object}
    @return: A python dictionary containing the
        items contained in I{sobject}.
    @rtype: dict
    """
    return dict(items(sobject))

def merge(a, b):
    """
    Merge all attributes and metadata from I{a} to I{b}.
    @param a: A I{source} object
    @type a: L{Object}
    @param b: A I{destination} object
    @type b: L{Object}
    """
    for item in a:
        setattr(b, item[0], item[1])
        b.__metadata__ = b.__metadata__
    return b

def footprint(sobject):
    """
    Get the I{virtual footprint} of the object.
    This is really a count of the attributes in the branch with a significant value.
    @param sobject: A suds object.
    @type sobject: L{Object}
    @return: The branch footprint.
    @rtype: int
    """
    n = 0
    for a in sobject.__keylist__:
        v = getattr(sobject, a)
        if v is None: continue
        if isinstance(v, Object):
            n += footprint(v)
            continue
        if hasattr(v, '__len__'):
            if len(v): n += 1
            continue
        n +=1
    return n

    
class Factory:
    
    cache = {}
    
    @classmethod
    def subclass(cls, name, bases, dict={}):
        if not isinstance(bases, tuple):
            bases = (bases,)
        name = name.encode('utf-8')
        key = '.'.join((name, str(bases)))
        subclass = cls.cache.get(key)
        if subclass is None:
            subclass = classobj(name, bases, dict)
            cls.cache[key] = subclass
        return subclass
    
    @classmethod
    def object(cls, classname=None, dict={}):
        if classname is not None:
            subclass = cls.subclass(classname, Object)
            inst = subclass()
        else:
            inst = Object()
        for a in dict.items():
            setattr(inst, a[0], a[1])
        return inst
    
    @classmethod
    def metadata(cls):
        return Metadata()
    
    @classmethod
    def property(cls, name, value=None):
        subclass = cls.subclass(name, Property)
        return subclass(value)


class Object:

    def __init__(self):
        self.__keylist__ = []
        self.__printer__ = Printer()
        self.__metadata__ = Metadata()

    def __setattr__(self, name, value):
        builtin =  name.startswith('__') and name.endswith('__')
        if not builtin and \
            name not in self.__keylist__:
            self.__keylist__.append(name)
        self.__dict__[name] = value
        
    def __delattr__(self, name):
        try:
            del self.__dict__[name]
            builtin =  name.startswith('__') and name.endswith('__')
            if not builtin:
                self.__keylist__.remove(name)
        except:
            cls = self.__class__.__name__
            raise AttributeError, "%s has no attribute '%s'" % (cls, name)

    def __getitem__(self, name):
        if isinstance(name, int):
            name = self.__keylist__[int(name)]
        return getattr(self, name)
    
    def __setitem__(self, name, value):
        setattr(self, name, value)
        
    def __iter__(self):
        return Iter(self)

    def __len__(self):
        return len(self.__keylist__)
    
    def __contains__(self, name):
        return name in self.__keylist__
    
    def __repr__(self):
        return str(self)

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.__printer__.tostr(self)


class Iter:

    def __init__(self, sobject):
        self.sobject = sobject
        self.keylist = self.__keylist(sobject)
        self.index = 0

    def next(self):
        keylist = self.keylist
        nkeys = len(self.keylist)
        while self.index < nkeys:
            k = keylist[self.index]
            self.index += 1
            if hasattr(self.sobject, k):
                v = getattr(self.sobject, k)
                return (k, v)
        raise StopIteration()
    
    def __keylist(self, sobject):
        keylist = sobject.__keylist__
        try:
            keyset = set(keylist)
            ordering = sobject.__metadata__.ordering
            ordered = set(ordering)
            if not ordered.issuperset(keyset):
                log.debug(
                    '%s must be superset of %s, ordering ignored',
                    keylist, 
                    ordering)
                raise KeyError()
            return ordering
        except:
            return keylist
        
    def __iter__(self):
        return self


class Metadata(Object):
    def __init__(self):
        self.__keylist__ = []
        self.__printer__ = Printer()


class Facade(Object):
    def __init__(self, name):
        Object.__init__(self)
        md = self.__metadata__
        md.facade = name

       
class Property(Object):

    def __init__(self, value):
        Object.__init__(self)
        self.value = value
        
    def items(self):
        for item in self:
            if item[0] != 'value':
                yield item
        
    def get(self):
        return self.value
    
    def set(self, value):
        self.value = value
        return self


class Printer:
    """ 
    Pretty printing of a Object object.
    """
    
    @classmethod
    def indent(cls, n): return '%*s'%(n*3,' ')

    def tostr(self, object, indent=-2):
        """ get s string representation of object """
        history = []
        return self.process(object, history, indent)
    
    def process(self, object, h, n=0, nl=False):
        """ print object using the specified indent (n) and newline (nl). """
        if object is None:
            return 'None'
        if isinstance(object, Object):
            if len(object) == 0:
                return '<empty>'
            else:
                return self.print_object(object, h, n+2, nl)
        if isinstance(object, dict):
            if len(object) == 0:
                return '<empty>'
            else:
                return self.print_dictionary(object, h, n+2, nl)
        if isinstance(object, (list,tuple)):
            if len(object) == 0:
                return '<empty>'
            else:
                return self.print_collection(object, h, n+2)
        if isinstance(object, basestring):
            return '"%s"' % tostr(object)
        return '%s' % tostr(object)
    
    def print_object(self, d, h, n, nl=False):
        """ print complex using the specified indent (n) and newline (nl). """
        s = []
        cls = d.__class__
        md = d.__metadata__
        if d in h:
            s.append('(')
            s.append(cls.__name__)
            s.append(')')
            s.append('...')
            return ''.join(s)
        h.append(d)
        if nl:
            s.append('\n')
            s.append(self.indent(n))
        if cls != Object:
            s.append('(')
            if isinstance(d, Facade):
                s.append(md.facade)
            else:
                s.append(cls.__name__)
            s.append(')')
        s.append('{')
        for item in d:
            if self.exclude(d, item):
                continue
            item = self.unwrap(d, item)
            s.append('\n')
            s.append(self.indent(n+1))
            if isinstance(item[1], (list,tuple)):            
                s.append(item[0])
                s.append('[]')
            else:
                s.append(item[0])
            s.append(' = ')
            s.append(self.process(item[1], h, n, True))
        s.append('\n')
        s.append(self.indent(n))
        s.append('}')
        h.pop()
        return ''.join(s)
    
    def print_dictionary(self, d, h, n, nl=False):
        """ print complex using the specified indent (n) and newline (nl). """
        if d in h: return '{}...'
        h.append(d)
        s = []
        if nl:
            s.append('\n')
            s.append(self.indent(n))
        s.append('{')
        for item in d.items():
            s.append('\n')
            s.append(self.indent(n+1))
            if isinstance(item[1], (list,tuple)):            
                s.append(tostr(item[0]))
                s.append('[]')
            else:
                s.append(tostr(item[0]))
            s.append(' = ')
            s.append(self.process(item[1], h, n, True))
        s.append('\n')
        s.append(self.indent(n))
        s.append('}')
        h.pop()
        return ''.join(s)

    def print_collection(self, c, h, n):
        """ print collection using the specified indent (n) and newline (nl). """
        if c in h: return '[]...'
        h.append(c)
        s = []
        for item in c:
            s.append('\n')
            s.append(self.indent(n))
            s.append(self.process(item, h, n-2))
            s.append(',')
        h.pop()
        return ''.join(s)
    
    def unwrap(self, d, item):
        """ translate (unwrap) using an optional wrapper function """
        nopt = ( lambda x: x )
        try:
            md = d.__metadata__
            pmd = getattr(md, '__print__', None)
            if pmd is None:
                return item
            wrappers = getattr(pmd, 'wrappers', {})
            fn = wrappers.get(item[0], nopt)
            return (item[0], fn(item[1]))
        except:
            pass
        return item
    
    def exclude(self, d, item):
        """ check metadata for excluded items """
        try:
            md = d.__metadata__
            pmd = getattr(md, '__print__', None)
            if pmd is None:
                return False
            excludes = getattr(pmd, 'excludes', [])
            return ( item[0] in excludes ) 
        except:
            pass
        return False