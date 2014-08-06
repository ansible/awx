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
Provides basic I{marshaller} classes.
"""

from logging import getLogger
from suds import *
from suds.mx import *
from suds.mx.core import Core

log = getLogger(__name__)


class Basic(Core):
    """
    A I{basic} (untyped) marshaller.
    """
    
    def process(self, value, tag=None):
        """
        Process (marshal) the tag with the specified value using the
        optional type information.
        @param value: The value (content) of the XML node.
        @type value: (L{Object}|any)
        @param tag: The (optional) tag name for the value.  The default is
            value.__class__.__name__
        @type tag: str
        @return: An xml node.
        @rtype: L{Element}
        """
        content = Content(tag=tag, value=value)
        result = Core.process(self, content)
        return result