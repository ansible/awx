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
The I{schema} module provides a intelligent representation of
an XSD schema.  The I{raw} model is the XML tree and the I{model}
is the denormalized, objectified and intelligent view of the schema.
Most of the I{value-add} provided by the model is centered around
tranparent referenced type resolution and targeted denormalization.
"""

from logging import getLogger
from suds import *
from suds.sax import Namespace, splitPrefix

log = getLogger(__name__)


def qualify(ref, resolvers, defns=Namespace.default):
    """
    Get a reference that is I{qualified} by namespace.
    @param ref: A referenced schema type name.
    @type ref: str
    @param resolvers: A list of objects to be used to resolve types.
    @type resolvers: [L{sax.element.Element},]
    @param defns: An optional target namespace used to qualify references
        when no prefix is specified.
    @type defns: A default namespace I{tuple: (prefix,uri)} used when ref not prefixed.
    @return: A qualified reference.
    @rtype: (name, namespace-uri)
    """
    ns = None
    p, n = splitPrefix(ref)
    if p is not None:
        if not isinstance(resolvers, (list, tuple)):
            resolvers = (resolvers,)
        for r in resolvers:
            resolved = r.resolvePrefix(p)
            if resolved[1] is not None:
                ns = resolved
                break
        if ns is None:
            raise Exception('prefix (%s) not resolved' % p)
    else:
        ns = defns
    return (n, ns[1])

def isqref(object):
    """
    Get whether the object is a I{qualified reference}.
    @param object: An object to be tested.
    @type object: I{any}
    @rtype: boolean
    @see: L{qualify}
    """
    return (\
        isinstance(object, tuple) and \
        len(object) == 2 and \
        isinstance(object[0], basestring) and \
        isinstance(object[1], basestring))


class Filter:
    def __init__(self, inclusive=False, *items):
        self.inclusive = inclusive
        self.items = items
    def __contains__(self, x):
        if self.inclusive:
            result = ( x in self.items )
        else:
            result = ( x not in self.items )
        return result

