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
The I{soaparray} module provides XSD extensions for handling
soap (section 5) encoded arrays.
"""

from suds import *
from logging import getLogger
from suds.xsd.sxbasic import Factory as SXFactory
from suds.xsd.sxbasic import Attribute as SXAttribute


class Attribute(SXAttribute):
    """
    Represents an XSD <attribute/> that handles special
    attributes that are extensions for WSDLs.
    @ivar aty: Array type information.
    @type aty: The value of wsdl:arrayType.
    """

    def __init__(self, schema, root, aty):
        """
        @param aty: Array type information.
        @type aty: The value of wsdl:arrayType.
        """
        SXAttribute.__init__(self, schema, root)
        if aty.endswith('[]'):
            self.aty = aty[:-2]
        else:
            self.aty = aty
        
    def autoqualified(self):
        aqs = SXAttribute.autoqualified(self)
        aqs.append('aty')
        return aqs
    
    def description(self):
        d = SXAttribute.description(self)
        d = d+('aty',)
        return d

#
# Builder function, only builds Attribute when arrayType
# attribute is defined on root.
#
def __fn(x, y):
    ns = (None, "http://schemas.xmlsoap.org/wsdl/")
    aty = y.get('arrayType', ns=ns)
    if aty is None:
        return SXAttribute(x, y)
    else:
        return Attribute(x, y, aty)

#
# Remap <xs:attrbute/> tags to __fn() builder.
#
SXFactory.maptag('attribute', __fn)