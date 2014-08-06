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
The I{service definition} provides a textual representation of a service.
"""

from logging import getLogger
from suds import *
import suds.metrics as metrics
from suds.sax import Namespace

log = getLogger(__name__)

class ServiceDefinition:
    """
    A service definition provides an object used to generate a textual description
    of a service.
    @ivar wsdl: A wsdl.
    @type wsdl: L{wsdl.Definitions}
    @ivar service: The service object.
    @type service: L{suds.wsdl.Service}
    @ivar ports: A list of port-tuple: (port, [(method-name, pdef)])
    @type ports: [port-tuple,..]
    @ivar prefixes: A list of remapped prefixes.
    @type prefixes: [(prefix,uri),..]
    @ivar types: A list of type definitions
    @type types: [I{Type},..] 
    """
    
    def __init__(self, wsdl, service):
        """
        @param wsdl: A wsdl object
        @type wsdl: L{Definitions}
        @param service: A service B{name}.
        @type service: str
        """
        self.wsdl = wsdl
        self.service = service
        self.ports = []
        self.params = []
        self.types = []
        self.prefixes = []
        self.addports()
        self.paramtypes()
        self.publictypes()
        self.getprefixes()
        self.pushprefixes()
    
    def pushprefixes(self):
        """
        Add our prefixes to the wsdl so that when users invoke methods
        and reference the prefixes, the will resolve properly.
        """
        for ns in self.prefixes:
            self.wsdl.root.addPrefix(ns[0], ns[1])

    def addports(self):
        """
        Look through the list of service ports and construct a list of tuples where
        each tuple is used to describe a port and it's list of methods as:
        (port, [method]).  Each method is tuple: (name, [pdef,..] where each pdef is
        a tuple: (param-name, type).
        """
        timer = metrics.Timer()
        timer.start()
        for port in self.service.ports:
            p = self.findport(port)
            for op in port.binding.operations.values():
                m = p[0].method(op.name)
                binding = m.binding.input
                method = (m.name, binding.param_defs(m))
                p[1].append(method)
                metrics.log.debug("method '%s' created: %s", m.name, timer)
            p[1].sort()
        timer.stop()
            
    def findport(self, port):
        """
        Find and return a port tuple for the specified port.
        Created and added when not found.
        @param port: A port.
        @type port: I{service.Port}
        @return: A port tuple.
        @rtype: (port, [method])
        """
        for p in self.ports:
            if p[0] == p: return p
        p = (port, [])
        self.ports.append(p)
        return p
            
    def getprefixes(self):
        """
        Add prefixes foreach namespace referenced by parameter types.
        """
        namespaces = []
        for l in (self.params, self.types):
            for t,r in l:
                ns = r.namespace()
                if ns[1] is None: continue
                if ns[1] in namespaces: continue
                if Namespace.xs(ns) or Namespace.xsd(ns):
                    continue
                namespaces.append(ns[1])
                if t == r: continue
                ns = t.namespace()
                if ns[1] is None: continue
                if ns[1] in namespaces: continue
                namespaces.append(ns[1])
        i = 0
        namespaces.sort()
        for u in namespaces:
            p = self.nextprefix()
            ns = (p, u)
            self.prefixes.append(ns)
            
    def paramtypes(self):
        """ get all parameter types """
        for m in [p[1] for p in self.ports]:
            for p in [p[1] for p in m]:
                for pd in p:
                    if pd[1] in self.params: continue
                    item = (pd[1], pd[1].resolve())
                    self.params.append(item)
                    
    def publictypes(self):
        """ get all public types """
        for t in self.wsdl.schema.types.values():
            if t in self.params: continue
            if t in self.types: continue
            item = (t, t)
            self.types.append(item)
        tc = lambda x,y: cmp(x[0].name, y[0].name)
        self.types.sort(cmp=tc)
        
    def nextprefix(self):
        """
        Get the next available prefix.  This means a prefix starting with 'ns' with
        a number appended as (ns0, ns1, ..) that is not already defined on the
        wsdl document.
        """
        used = [ns[0] for ns in self.prefixes]
        used += [ns[0] for ns in self.wsdl.root.nsprefixes.items()]
        for n in range(0,1024):
            p = 'ns%d'%n
            if p not in used:
                return p
        raise Exception('prefixes exhausted')
    
    def getprefix(self, u):
        """
        Get the prefix for the specified namespace (uri)
        @param u: A namespace uri.
        @type u: str
        @return: The namspace.
        @rtype: (prefix, uri).
        """
        for ns in Namespace.all:
            if u == ns[1]: return ns[0]
        for ns in self.prefixes:
            if u == ns[1]: return ns[0]
        raise Exception('ns (%s) not mapped'  % u)
    
    def xlate(self, type):
        """
        Get a (namespace) translated I{qualified} name for specified type.
        @param type: A schema type.
        @type type: I{suds.xsd.sxbasic.SchemaObject}
        @return: A translated I{qualified} name.
        @rtype: str
        """
        resolved = type.resolve()
        name = resolved.name
        if type.unbounded():
            name += '[]'
        ns = resolved.namespace()
        if ns[1] == self.wsdl.tns[1]:
            return name
        prefix = self.getprefix(ns[1])
        return ':'.join((prefix, name))
        
    def description(self):
        """
        Get a textual description of the service for which this object represents.
        @return: A textual description.
        @rtype: str
        """
        s = []
        indent = (lambda n :  '\n%*s'%(n*3,' '))
        s.append('Service ( %s ) tns="%s"' % (self.service.name, self.wsdl.tns[1]))
        s.append(indent(1))
        s.append('Prefixes (%d)' % len(self.prefixes))
        for p in self.prefixes:
            s.append(indent(2))
            s.append('%s = "%s"' % p)
        s.append(indent(1))
        s.append('Ports (%d):' % len(self.ports))
        for p in self.ports:
            s.append(indent(2))
            s.append('(%s)' % p[0].name)
            s.append(indent(3))
            s.append('Methods (%d):' % len(p[1]))
            for m in p[1]:
                sig = []
                s.append(indent(4))
                sig.append(m[0])
                sig.append('(')
                for p in m[1]:
                    sig.append(self.xlate(p[1]))
                    sig.append(' ')
                    sig.append(p[0])
                    sig.append(', ')
                sig.append(')')
                try:
                    s.append(''.join(sig))
                except:
                    pass
            s.append(indent(3))
            s.append('Types (%d):' % len(self.types))
            for t in self.types:
                s.append(indent(4))
                s.append(self.xlate(t[0]))
        s.append('\n\n')
        return ''.join(s)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
        
    def __unicode__(self):
        try:
            return self.description()
        except Exception, e:
            log.exception(e)
        return tostr(e)