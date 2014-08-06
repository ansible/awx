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
Provides soap encoded unmarshaller classes.
"""

from logging import getLogger
from suds import *
from suds.umx import *
from suds.umx.typed import Typed
from suds.sax import splitPrefix, Namespace

log = getLogger(__name__)

#
# Add encoded extensions
# aty = The soap (section 5) encoded array type.
#
Content.extensions.append('aty')


class Encoded(Typed):
    """
    A SOAP section (5) encoding unmarshaller.
    This marshaller supports rpc/encoded soap styles.
    """

    def start(self, content):
        #
        # Grab the array type and continue
        #
        self.setaty(content)
        Typed.start(self, content)
    
    def end(self, content):
        #
        # Squash soap encoded arrays into python lists.  This is
        # also where we insure that empty arrays are represented
        # as empty python lists.
        #
        aty = content.aty
        if aty is not None:
            self.promote(content)
        return Typed.end(self, content)
    
    def postprocess(self, content):
        #
        # Ensure proper rendering of empty arrays.
        #
        if content.aty is None:
            return Typed.postprocess(self, content)
        else:
            return content.data
    
    def setaty(self, content):
        """
        Grab the (aty) soap-enc:arrayType and attach it to the
        content for proper array processing later in end().
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        @return: self
        @rtype: L{Encoded}
        """
        name = 'arrayType'
        ns = (None, 'http://schemas.xmlsoap.org/soap/encoding/')
        aty = content.node.get(name, ns)
        if aty is not None:
            content.aty = aty
            parts = aty.split('[')
            ref = parts[0]
            if len(parts) == 2:
                self.applyaty(content, ref)
            else:
                pass # (2) dimensional array
        return self
    
    def applyaty(self, content, xty):
        """
        Apply the type referenced in the I{arrayType} to the content
        (child nodes) of the array.  Each element (node) in the array 
        that does not have an explicit xsi:type attribute is given one
        based on the I{arrayType}.
        @param content: An array content.
        @type content: L{Content}
        @param xty: The XSI type reference.
        @type xty: str
        @return: self
        @rtype: L{Encoded}
        """
        name = 'type'
        ns = Namespace.xsins
        parent = content.node
        for child in parent.getChildren():
            ref = child.get(name, ns)
            if ref is None:
                parent.addPrefix(ns[0], ns[1])
                attr = ':'.join((ns[0], name))
                child.set(attr, xty)
        return self

    def promote(self, content):
        """
        Promote (replace) the content.data with the first attribute
        of the current content.data that is a I{list}.  Note: the 
        content.data may be empty or contain only _x attributes.
        In either case, the content.data is assigned an empty list.
        @param content: An array content.
        @type content: L{Content}
        """
        for n,v in content.data:
            if isinstance(v, list):
                content.data = v
                return
        content.data = []