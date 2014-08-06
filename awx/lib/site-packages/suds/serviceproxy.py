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
The service proxy provides access to web services.

Replaced by: L{client.Client}
"""

from logging import getLogger
from suds import *
from suds.client import Client

log = getLogger(__name__)


class ServiceProxy(object):
    
    """ 
    A lightweight soap based web service proxy.
    @ivar __client__: A client.  
        Everything is delegated to the 2nd generation API.
    @type __client__: L{Client}
    @note:  Deprecated, replaced by L{Client}.
    """

    def __init__(self, url, **kwargs):
        """
        @param url: The URL for the WSDL.
        @type url: str
        @param kwargs: keyword arguments.
        @keyword faults: Raise faults raised by server (default:True),
                else return tuple from service method invocation as (http code, object).
        @type faults: boolean
        @keyword proxy: An http proxy to be specified on requests (default:{}).
                           The proxy is defined as {protocol:proxy,}
        @type proxy: dict
        """
        client = Client(url, **kwargs)
        self.__client__ = client
    
    def get_instance(self, name):
        """
        Get an instance of a WSDL type by name
        @param name: The name of a type defined in the WSDL.
        @type name: str
        @return: An instance on success, else None
        @rtype: L{sudsobject.Object}
        """
        return self.__client__.factory.create(name)
    
    def get_enum(self, name):
        """
        Get an instance of an enumeration defined in the WSDL by name.
        @param name: The name of a enumeration defined in the WSDL.
        @type name: str
        @return: An instance on success, else None
        @rtype: L{sudsobject.Object}
        """
        return self.__client__.factory.create(name)
 
    def __str__(self):
        return str(self.__client__)
        
    def __unicode__(self):
        return unicode(self.__client__)
    
    def __getattr__(self, name):
        builtin =  name.startswith('__') and name.endswith('__')
        if builtin:
            return self.__dict__[name]
        else:
            return getattr(self.__client__.service, name)