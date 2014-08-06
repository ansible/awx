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
Suds basic options classes.
"""

from suds.properties import *
from suds.wsse import Security
from suds.xsd.doctor import Doctor
from suds.transport import Transport
from suds.cache import Cache, NoCache


class TpLinker(AutoLinker):
    """
    Transport (auto) linker used to manage linkage between
    transport objects Properties and those Properties that contain them.
    """
    
    def updated(self, properties, prev, next):
        if isinstance(prev, Transport):
            tp = Unskin(prev.options)
            properties.unlink(tp)
        if isinstance(next, Transport):
            tp = Unskin(next.options)
            properties.link(tp)


class Options(Skin):
    """
    Options:
        - B{cache} - The XML document cache.  May be set (None) for no caching.
                - type: L{Cache}
                - default: L{NoCache}
        - B{faults} - Raise faults raised by server,
            else return tuple from service method invocation as (httpcode, object).
                - type: I{bool}
                - default: True
        - B{service} - The default service name.
                - type: I{str}
                - default: None
        - B{port} - The default service port name, not tcp port.
                - type: I{str}
                - default: None
        - B{location} - This overrides the service port address I{URL} defined 
            in the WSDL.
                - type: I{str}
                - default: None
        - B{transport} - The message transport.
                - type: L{Transport}
                - default: None
        - B{soapheaders} - The soap headers to be included in the soap message.
                - type: I{any}
                - default: None
        - B{wsse} - The web services I{security} provider object.
                - type: L{Security}
                - default: None
        - B{doctor} - A schema I{doctor} object.
                - type: L{Doctor}
                - default: None
        - B{xstq} - The B{x}ml B{s}chema B{t}ype B{q}ualified flag indicates
            that the I{xsi:type} attribute values should be qualified by namespace.
                - type: I{bool}
                - default: True
        - B{prefixes} - Elements of the soap message should be qualified (when needed)
            using XML prefixes as opposed to xmlns="" syntax.
                - type: I{bool}
                - default: True
        - B{retxml} - Flag that causes the I{raw} soap envelope to be returned instead
            of the python object graph.
                - type: I{bool}
                - default: False
        - B{prettyxml} - Flag that causes I{pretty} xml to be rendered when generating
            the outbound soap envelope.
                - type: I{bool}
                - default: False
        - B{autoblend} - Flag that ensures that the schema(s) defined within the
            WSDL import each other.
                - type: I{bool}
                - default: False
        - B{cachingpolicy} - The caching policy.
                - type: I{int}
                  - 0 = Cache XML documents.
                  - 1 = Cache WSDL (pickled) object.
                - default: 0
        - B{plugins} - A plugin container.
                - type: I{list}
    """    
    def __init__(self, **kwargs):
        domain = __name__
        definitions = [
            Definition('cache', Cache, NoCache()),
            Definition('faults', bool, True),
            Definition('transport', Transport, None, TpLinker()),
            Definition('service', (int, basestring), None),
            Definition('port', (int, basestring), None),
            Definition('location', basestring, None),
            Definition('soapheaders', (), ()),
            Definition('wsse', Security, None),
            Definition('doctor', Doctor, None),
            Definition('xstq', bool, True),
            Definition('prefixes', bool, True),
            Definition('retxml', bool, False),
            Definition('prettyxml', bool, False),
            Definition('autoblend', bool, False),
            Definition('cachingpolicy', int, 0),
            Definition('plugins', (list, tuple), []),
        ]
        Skin.__init__(self, domain, definitions, kwargs)
