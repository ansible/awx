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
The I{query} module defines a class for performing schema queries.
"""

from logging import getLogger
from suds import *
from suds.sudsobject import *
from suds.xsd import qualify, isqref
from suds.xsd.sxbuiltin import Factory

log = getLogger(__name__)


class Query(Object):
    """
    Schema query base class.
    """
    
    def __init__(self, ref=None):
        """
        @param ref: The schema reference being queried.
        @type ref: qref
        """
        Object.__init__(self)
        self.id = objid(self)
        self.ref = ref
        self.history = []
        self.resolved = False
        if not isqref(self.ref):
            raise Exception('%s, must be qref' % tostr(self.ref))
        
    def execute(self, schema):
        """
        Execute this query using the specified schema.
        @param schema: The schema associated with the query.  The schema
            is used by the query to search for items.
        @type schema: L{schema.Schema}
        @return: The item matching the search criteria.
        @rtype: L{sxbase.SchemaObject}
        """
        raise Exception, 'not-implemented by subclass'
        
    def filter(self, result):
        """
        Filter the specified result based on query criteria.
        @param result: A potential result.
        @type result: L{sxbase.SchemaObject}
        @return: True if result should be excluded.
        @rtype: boolean
        """
        if result is None:
            return True
        reject = ( result in self.history )
        if reject:
            log.debug('result %s, rejected by\n%s', Repr(result), self)
        return reject
    
    def result(self, result):
        """
        Query result post processing.
        @param result: A query result.
        @type result: L{sxbase.SchemaObject}
        """
        if result is None:
            log.debug('%s, not-found', self.ref)
            return
        if self.resolved:
            result = result.resolve()
        log.debug('%s, found as: %s', self.ref, Repr(result))
        self.history.append(result)
        return result


class BlindQuery(Query):
    """
    Schema query class that I{blindly} searches for a reference in
    the specified schema.  It may be used to find Elements and Types but
    will match on an Element first.  This query will also find builtins.
    """
        
    def execute(self, schema):
        if schema.builtin(self.ref):
            name = self.ref[0]
            b = Factory.create(schema, name)
            log.debug('%s, found builtin (%s)', self.id, name)
            return b
        result = None
        for d in (schema.elements, schema.types):
            result = d.get(self.ref)
            if self.filter(result):
                result = None
            else:
                break
        if result is None:
            eq = ElementQuery(self.ref)
            eq.history = self.history
            result = eq.execute(schema)
        return self.result(result)


class TypeQuery(Query):
    """
    Schema query class that searches for Type references in
    the specified schema.  Matches on root types only.
    """
        
    def execute(self, schema):
        if schema.builtin(self.ref):
            name = self.ref[0]
            b = Factory.create(schema, name)
            log.debug('%s, found builtin (%s)', self.id, name)
            return b
        result = schema.types.get(self.ref)
        if self.filter(result):
            result = None
        return self.result(result)


class GroupQuery(Query):
    """
    Schema query class that searches for Group references in
    the specified schema.
    """
        
    def execute(self, schema):
        result = schema.groups.get(self.ref)
        if self.filter(result):
            result = None
        return self.result(result)


class AttrQuery(Query):
    """
    Schema query class that searches for Attribute references in
    the specified schema.  Matches on root Attribute by qname first, then searches
    deep into the document.
    """
        
    def execute(self, schema):
        result = schema.attributes.get(self.ref)
        if self.filter(result):
            result = self.__deepsearch(schema)
        return self.result(result)
    
    def __deepsearch(self, schema):
        from suds.xsd.sxbasic import Attribute
        result = None
        for e in schema.all:
            result = e.find(self.ref, (Attribute,))
            if self.filter(result):
                result = None
            else:
                break
        return result


class AttrGroupQuery(Query):
    """
    Schema query class that searches for attributeGroup references in
    the specified schema.
    """
        
    def execute(self, schema):
        result = schema.agrps.get(self.ref)
        if self.filter(result):
            result = None
        return self.result(result)


class ElementQuery(Query):
    """
    Schema query class that searches for Element references in
    the specified schema.  Matches on root Elements by qname first, then searches
    deep into the document.
    """
        
    def execute(self, schema):
        result = schema.elements.get(self.ref)
        if self.filter(result):
            result = self.__deepsearch(schema)
        return self.result(result)
    
    def __deepsearch(self, schema):
        from suds.xsd.sxbasic import Element
        result = None
        for e in schema.all:
            result = e.find(self.ref, (Element,))
            if self.filter(result):
                result = None
            else:
                break
        return result