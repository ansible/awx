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
Contains classes for transport options.
"""


from suds.transport import *
from suds.properties import *

   
class Options(Skin):
    """
    Options:
        - B{proxy} - An http proxy to be specified on requests.
             The proxy is defined as {protocol:proxy,}
                - type: I{dict}
                - default: {}
        - B{timeout} - Set the url open timeout (seconds).
                - type: I{float}
                - default: 90
        - B{headers} - Extra HTTP headers.
                - type: I{dict}
                    - I{str} B{http} - The I{http} protocol proxy URL.
                    - I{str} B{https} - The I{https} protocol proxy URL.
                - default: {}
        - B{username} - The username used for http authentication.
                - type: I{str}
                - default: None
        - B{password} - The password used for http authentication.
                - type: I{str}
                - default: None
    """    
    def __init__(self, **kwargs):
        domain = __name__
        definitions = [
            Definition('proxy', dict, {}),
            Definition('timeout', (int,float), 90),
            Definition('headers', dict, {}),
            Definition('username', basestring, None),
            Definition('password', basestring, None),
        ]
        Skin.__init__(self, domain, definitions, kwargs)