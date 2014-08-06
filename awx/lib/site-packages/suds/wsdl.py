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
The I{wsdl} module provides an objectification of the WSDL.
The primary class is I{Definitions} as it represends the root element
found in the document.
"""

from logging import getLogger
from suds import *
from suds.sax import splitPrefix
from suds.sax.element import Element
from suds.bindings.document import Document
from suds.bindings.rpc import RPC, Encoded
from suds.xsd import qualify, Namespace
from suds.xsd.schema import Schema, SchemaCollection
from suds.xsd.query import ElementQuery
from suds.sudsobject import Object, Facade, Metadata
from suds.reader import DocumentReader, DefinitionsReader
from urlparse import urljoin
import re, soaparray

log = getLogger(__name__)

wsdlns = (None, "http://schemas.xmlsoap.org/wsdl/")
soapns = (None, 'http://schemas.xmlsoap.org/wsdl/soap/')
soap12ns = (None, 'http://schemas.xmlsoap.org/wsdl/soap12/')


class WObject(Object):
    """
    Base object for wsdl types.
    @ivar root: The XML I{root} element.
    @type root: L{Element}
    """
    
    def __init__(self, root, definitions=None):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        Object.__init__(self)
        self.root = root
        pmd = Metadata()
        pmd.excludes = ['root']
        pmd.wrappers = dict(qname=repr)
        self.__metadata__.__print__ = pmd
        
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        pass

        
class NamedObject(WObject):
    """
    A B{named} WSDL object.
    @ivar name: The name of the object.
    @type name: str
    @ivar qname: The I{qualified} name of the object.
    @type qname: (name, I{namespace-uri}).
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        WObject.__init__(self, root, definitions)
        self.name = root.get('name')
        self.qname = (self.name, definitions.tns[1])
        pmd = self.__metadata__.__print__
        pmd.wrappers['qname'] = repr


class Definitions(WObject):
    """
    Represents the I{root} container of the WSDL objects as defined
    by <wsdl:definitions/>
    @ivar id: The object id.
    @type id: str
    @ivar options: An options dictionary.
    @type options: L{options.Options}
    @ivar url: The URL used to load the object.
    @type url: str
    @ivar tns: The target namespace for the WSDL.
    @type tns: str
    @ivar schema: The collective WSDL schema object.
    @type schema: L{SchemaCollection}
    @ivar children: The raw list of child objects.
    @type children: [L{WObject},...]
    @ivar imports: The list of L{Import} children.
    @type imports: [L{Import},...]
    @ivar messages: The dictionary of L{Message} children key'd by I{qname}
    @type messages: [L{Message},...]
    @ivar port_types: The dictionary of L{PortType} children key'd by I{qname}
    @type port_types: [L{PortType},...]
    @ivar bindings: The dictionary of L{Binding} children key'd by I{qname}
    @type bindings: [L{Binding},...]
    @ivar service: The service object.
    @type service: L{Service}
    """
    
    Tag = 'definitions'

    def __init__(self, url, options):
        """
        @param url: A URL to the WSDL.
        @type url: str
        @param options: An options dictionary.
        @type options: L{options.Options}
        """
        log.debug('reading wsdl at: %s ...', url)
        reader = DocumentReader(options)
        d = reader.open(url)
        root = d.root()
        WObject.__init__(self, root)
        self.id = objid(self)
        self.options = options
        self.url = url
        self.tns = self.mktns(root)
        self.types = []
        self.schema = None
        self.children = []
        self.imports = []
        self.messages = {}
        self.port_types = {}
        self.bindings = {}
        self.services = []
        self.add_children(self.root)
        self.children.sort()
        pmd = self.__metadata__.__print__
        pmd.excludes.append('children')
        pmd.excludes.append('wsdl')
        pmd.wrappers['schema'] = repr
        self.open_imports()
        self.resolve()
        self.build_schema()
        self.set_wrapped()
        for s in self.services:
            self.add_methods(s)
        log.debug("wsdl at '%s' loaded:\n%s", url, self)
        
    def mktns(self, root):
        """ Get/create the target namespace """
        tns = root.get('targetNamespace')
        prefix = root.findPrefix(tns)
        if prefix is None:
            log.debug('warning: tns (%s), not mapped to prefix', tns)
            prefix = 'tns'
        return (prefix, tns)
        
    def add_children(self, root):
        """ Add child objects using the factory """
        for c in root.getChildren(ns=wsdlns):
            child = Factory.create(c, self)
            if child is None: continue
            self.children.append(child)
            if isinstance(child, Import):
                self.imports.append(child)
                continue
            if isinstance(child, Types):
                self.types.append(child)
                continue
            if isinstance(child, Message):
                self.messages[child.qname] = child
                continue
            if isinstance(child, PortType):
                self.port_types[child.qname] = child
                continue
            if isinstance(child, Binding):
                self.bindings[child.qname] = child
                continue
            if isinstance(child, Service):
                self.services.append(child)
                continue
                
    def open_imports(self):
        """ Import the I{imported} WSDLs. """
        for imp in self.imports:
            imp.load(self)
                
    def resolve(self):
        """ Tell all children to resolve themselves """
        for c in self.children:
            c.resolve(self)
                
    def build_schema(self):
        """ Process L{Types} objects and create the schema collection """
        container = SchemaCollection(self)
        for t in [t for t in self.types if t.local()]:
            for root in t.contents():
                schema = Schema(root, self.url, self.options, container)
                container.add(schema)
        if not len(container): # empty
            root = Element.buildPath(self.root, 'types/schema')
            schema = Schema(root, self.url, self.options, container)
            container.add(schema)
        self.schema = container.load(self.options)
        for s in [t.schema() for t in self.types if t.imported()]:
            self.schema.merge(s)
        return self.schema
                
    def add_methods(self, service):
        """ Build method view for service """
        bindings = {
            'document/literal' : Document(self),
            'rpc/literal' : RPC(self),
            'rpc/encoded' : Encoded(self)
        }
        for p in service.ports:
            binding = p.binding
            ptype = p.binding.type
            operations = p.binding.type.operations.values()
            for name in [op.name for op in operations]:
                m = Facade('Method')
                m.name = name
                m.location = p.location
                m.binding = Facade('binding')
                op = binding.operation(name)
                m.soap = op.soap
                key = '/'.join((op.soap.style, op.soap.input.body.use))
                m.binding.input = bindings.get(key)
                key = '/'.join((op.soap.style, op.soap.output.body.use))
                m.binding.output = bindings.get(key)
                op = ptype.operation(name)
                p.methods[name] = m
                
    def set_wrapped(self):
        """ set (wrapped|bare) flag on messages """
        for b in self.bindings.values():
            for op in b.operations.values():
                for body in (op.soap.input.body, op.soap.output.body):
                    body.wrapped = False
                    if len(body.parts) != 1:
                        continue
                    for p in body.parts:
                        if p.element is None:
                            continue
                        query = ElementQuery(p.element)
                        pt = query.execute(self.schema)
                        if pt is None:
                            raise TypeNotFound(query.ref)
                        resolved = pt.resolve()
                        if resolved.builtin():
                            continue
                        body.wrapped = True
                        
    def __getstate__(self):
        nopickle = ('options',)
        state = self.__dict__.copy()
        for k in nopickle:
            if k in state:
                del state[k]
        return state
    
    def __repr__(self):
        return 'Definitions (id=%s)' % self.id


class Import(WObject):
    """
    Represents the <wsdl:import/>.
    @ivar location: The value of the I{location} attribute.
    @type location: str
    @ivar ns: The value of the I{namespace} attribute.
    @type ns: str
    @ivar imported: The imported object.
    @type imported: L{Definitions}
    """
    
    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        WObject.__init__(self, root, definitions)
        self.location = root.get('location')
        self.ns = root.get('namespace')
        self.imported = None
        pmd = self.__metadata__.__print__
        pmd.wrappers['imported'] = repr
        
    def load(self, definitions):
        """ Load the object by opening the URL """
        url = self.location
        log.debug('importing (%s)', url)
        if '://' not in url:
            url = urljoin(definitions.url, url)
        options = definitions.options
        d = Definitions(url, options)
        if d.root.match(Definitions.Tag, wsdlns):
            self.import_definitions(definitions, d)
            return
        if d.root.match(Schema.Tag, Namespace.xsdns):
            self.import_schema(definitions, d)
            return
        raise Exception('document at "%s" is unknown' % url)
    
    def import_definitions(self, definitions, d):
        """ import/merge wsdl definitions """
        definitions.types += d.types
        definitions.messages.update(d.messages)
        definitions.port_types.update(d.port_types)
        definitions.bindings.update(d.bindings)
        self.imported = d
        log.debug('imported (WSDL):\n%s', d)
        
    def import_schema(self, definitions, d):
        """ import schema as <types/> content """
        if not len(definitions.types):
            types = Types.create(definitions)
            definitions.types.append(types)
        else:
            types = definitions.types[-1]
        types.root.append(d.root)
        log.debug('imported (XSD):\n%s', d.root)
   
    def __gt__(self, other):
        return False
        

class Types(WObject):
    """
    Represents <types><schema/></types>.
    """
    
    @classmethod
    def create(cls, definitions):
        root = Element('types', ns=wsdlns)
        definitions.root.insert(root)
        return Types(root, definitions)

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        WObject.__init__(self, root, definitions)
        self.definitions = definitions
        
    def contents(self):
        return self.root.getChildren('schema', Namespace.xsdns)
    
    def schema(self):
        return self.definitions.schema
    
    def local(self):
        return ( self.definitions.schema is None )
    
    def imported(self):
        return ( not self.local() )
        
    def __gt__(self, other):
        return isinstance(other, Import)
    

class Part(NamedObject):
    """
    Represents <message><part/></message>.
    @ivar element: The value of the {element} attribute.
        Stored as a I{qref} as converted by L{suds.xsd.qualify}.
    @type element: str
    @ivar type: The value of the {type} attribute.
        Stored as a I{qref} as converted by L{suds.xsd.qualify}.
    @type type: str
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        pmd = Metadata()
        pmd.wrappers = dict(element=repr, type=repr)
        self.__metadata__.__print__ = pmd
        tns = definitions.tns
        self.element = self.__getref('element', tns)
        self.type = self.__getref('type', tns)
        
    def __getref(self, a, tns):
        """ Get the qualified value of attribute named 'a'."""
        s = self.root.get(a)
        if s is None:
            return s
        else:
            return qualify(s, self.root, tns)  


class Message(NamedObject):
    """
    Represents <message/>.
    @ivar parts: A list of message parts.
    @type parts: [I{Part},...]
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.parts = []
        for p in root.getChildren('part'):
            part = Part(p, definitions)
            self.parts.append(part)
            
    def __gt__(self, other):
        return isinstance(other, (Import, Types))
    
    
class PortType(NamedObject):
    """
    Represents <portType/>.
    @ivar operations: A list of contained operations.
    @type operations: list
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.operations = {}
        for c in root.getChildren('operation'):
            op = Facade('Operation')
            op.name = c.get('name')
            op.tns = definitions.tns
            input = c.getChild('input')
            if input is None:
                op.input = None
            else:
                op.input = input.get('message')
            output = c.getChild('output')
            if output is None:
                op.output = None
            else:
                op.output = output.get('message')
            faults = []
            for fault in c.getChildren('fault'):
                f = Facade('Fault')
                f.name = fault.get('name')
                f.message = fault.get('message')
                faults.append(f)
            op.faults = faults
            self.operations[op.name] = op
            
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        for op in self.operations.values():
            if op.input is None:
                op.input = Message(Element('no-input'), definitions)
            else:
                qref = qualify(op.input, self.root, definitions.tns)
                msg = definitions.messages.get(qref)
                if msg is None:
                    raise Exception("msg '%s', not-found" % op.input)
                else:
                    op.input = msg
            if op.output is None:
                op.output = Message(Element('no-output'), definitions)
            else:
                qref = qualify(op.output, self.root, definitions.tns)
                msg = definitions.messages.get(qref)
                if msg is None:
                    raise Exception("msg '%s', not-found" % op.output)
                else:
                    op.output = msg
            for f in op.faults:
                qref = qualify(f.message, self.root, definitions.tns)
                msg = definitions.messages.get(qref)
                if msg is None:
                    raise Exception, "msg '%s', not-found" % f.message
                f.message = msg
                
    def operation(self, name):
        """
        Shortcut used to get a contained operation by name.
        @param name: An operation name.
        @type name: str
        @return: The named operation.
        @rtype: Operation
        @raise L{MethodNotFound}: When not found.
        """
        try:
            return self.operations[name]
        except Exception, e:
            raise MethodNotFound(name)
                
    def __gt__(self, other):
        return isinstance(other, (Import, Types, Message))


class Binding(NamedObject):
    """
    Represents <binding/>
    @ivar operations: A list of contained operations.
    @type operations: list
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.operations = {}
        self.type = root.get('type')
        sr = self.soaproot()
        if sr is None:
            self.soap = None
            log.debug('binding: "%s" not a soap binding', self.name)
            return
        soap = Facade('soap')
        self.soap = soap
        self.soap.style = sr.get('style', default='document')
        self.add_operations(self.root, definitions)
        
    def soaproot(self):
        """ get the soap:binding """
        for ns in (soapns, soap12ns):
            sr =  self.root.getChild('binding', ns=ns)
            if sr is not None:
                return sr
        return None
        
    def add_operations(self, root, definitions):
        """ Add <operation/> children """
        dsop = Element('operation', ns=soapns)
        for c in root.getChildren('operation'):
            op = Facade('Operation')
            op.name = c.get('name')
            sop = c.getChild('operation', default=dsop)
            soap = Facade('soap')
            soap.action = '"%s"' % sop.get('soapAction', default='')
            soap.style = sop.get('style', default=self.soap.style)
            soap.input = Facade('Input')
            soap.input.body = Facade('Body')
            soap.input.headers = []
            soap.output = Facade('Output')
            soap.output.body = Facade('Body')
            soap.output.headers = []
            op.soap = soap
            input = c.getChild('input')
            if input is None:
                input = Element('input', ns=wsdlns)
            body = input.getChild('body')
            self.body(definitions, soap.input.body, body)
            for header in input.getChildren('header'):
                self.header(definitions, soap.input, header)
            output = c.getChild('output')
            if output is None:
                output = Element('output', ns=wsdlns)
            body = output.getChild('body')
            self.body(definitions, soap.output.body, body)
            for header in output.getChildren('header'):
                self.header(definitions, soap.output, header)
            faults = []
            for fault in c.getChildren('fault'):
                sf = fault.getChild('fault')
                if sf is None:
                    continue
                fn = fault.get('name')
                f = Facade('Fault')
                f.name = sf.get('name', default=fn)
                f.use = sf.get('use', default='literal')
                faults.append(f)
            soap.faults = faults
            self.operations[op.name] = op
            
    def body(self, definitions, body, root):
        """ add the input/output body properties """
        if root is None:
            body.use = 'literal'
            body.namespace = definitions.tns
            body.parts = ()
            return
        parts = root.get('parts')
        if parts is None:
            body.parts = ()
        else:
            body.parts = re.split('[\s,]', parts)
        body.use = root.get('use', default='literal')
        ns = root.get('namespace')
        if ns is None:
            body.namespace = definitions.tns
        else:
            prefix = root.findPrefix(ns, 'b0')
            body.namespace = (prefix, ns)
            
    def header(self, definitions, parent, root):
        """ add the input/output header properties """
        if root is None:
            return
        header = Facade('Header')
        parent.headers.append(header)
        header.use = root.get('use', default='literal')
        ns = root.get('namespace')
        if ns is None:
            header.namespace = definitions.tns
        else:
            prefix = root.findPrefix(ns, 'h0')
            header.namespace = (prefix, ns)
        msg = root.get('message')
        if msg is not None:
            header.message = msg
        part = root.get('part')
        if part is not None:
            header.part = part
            
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.  This includes
        cross-linking information (from) the portType (to) the I{soap}
        protocol information on the binding for each operation.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        self.resolveport(definitions)
        for op in self.operations.values():
            self.resolvesoapbody(definitions, op)
            self.resolveheaders(definitions, op)
            self.resolvefaults(definitions, op)
        
    def resolveport(self, definitions):
        """
        Resolve port_type reference.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        ref = qualify(self.type, self.root, definitions.tns)
        port_type = definitions.port_types.get(ref)
        if port_type is None:
            raise Exception("portType '%s', not-found" % self.type)
        else:
            self.type = port_type
            
    def resolvesoapbody(self, definitions, op):
        """
        Resolve soap body I{message} parts by 
        cross-referencing with operation defined in port type.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        @param op: An I{operation} object.
        @type op: I{operation}
        """
        ptop = self.type.operation(op.name)
        if ptop is None:
            raise Exception, \
                "operation '%s' not defined in portType" % op.name
        soap = op.soap
        parts = soap.input.body.parts
        if len(parts):
            pts = []
            for p in ptop.input.parts:
                if p.name in parts:
                    pts.append(p)
            soap.input.body.parts = pts
        else:
            soap.input.body.parts = ptop.input.parts
        parts = soap.output.body.parts
        if len(parts):
            pts = []
            for p in ptop.output.parts:
                if p.name in parts:
                    pts.append(p)
            soap.output.body.parts = pts
        else:
            soap.output.body.parts = ptop.output.parts
            
    def resolveheaders(self, definitions, op):
        """
        Resolve soap header I{message} references.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        @param op: An I{operation} object.
        @type op: I{operation}
        """
        soap = op.soap
        headers = soap.input.headers + soap.output.headers
        for header in headers:
            mn = header.message
            ref = qualify(mn, self.root, definitions.tns)
            message = definitions.messages.get(ref)
            if message is None:
                raise Exception, "message'%s', not-found" % mn
            pn = header.part
            for p in message.parts:
                if p.name == pn:
                    header.part = p
                    break
            if pn == header.part:
                raise Exception, \
                    "message '%s' has not part named '%s'" % (ref, pn)
                        
    def resolvefaults(self, definitions, op):
        """
        Resolve soap fault I{message} references by
        cross-referencing with operation defined in port type.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        @param op: An I{operation} object.
        @type op: I{operation}
        """
        ptop = self.type.operation(op.name)
        if ptop is None:
            raise Exception, \
                "operation '%s' not defined in portType" % op.name
        soap = op.soap
        for fault in soap.faults:
            for f in ptop.faults:
                if f.name == fault.name:
                    fault.parts = f.message.parts
                    continue
            if hasattr(fault, 'parts'):
                continue
            raise Exception, \
                "fault '%s' not defined in portType '%s'" % (fault.name, self.type.name)
            
    def operation(self, name):
        """
        Shortcut used to get a contained operation by name.
        @param name: An operation name.
        @type name: str
        @return: The named operation.
        @rtype: Operation
        @raise L{MethodNotFound}: When not found.
        """
        try:
            return self.operations[name]
        except:
            raise MethodNotFound(name)
            
    def __gt__(self, other):
        return ( not isinstance(other, Service) )


class Port(NamedObject):
    """
    Represents a service port.
    @ivar service: A service.
    @type service: L{Service}
    @ivar binding: A binding name.
    @type binding: str
    @ivar location: The service location (url).
    @type location: str
    """
    
    def __init__(self, root, definitions, service):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        @param service: A service object.
        @type service: L{Service}
        """
        NamedObject.__init__(self, root, definitions)
        self.__service = service
        self.binding = root.get('binding')
        address = root.getChild('address')
        if address is None:
            self.location = None
        else:
            self.location = address.get('location').encode('utf-8')
        self.methods = {}
        
    def method(self, name):
        """
        Get a method defined in this portType by name.
        @param name: A method name.
        @type name: str
        @return: The requested method object.
        @rtype: I{Method}
        """
        return self.methods.get(name)
        

class Service(NamedObject):
    """
    Represents <service/>.
    @ivar port: The contained ports.
    @type port: [Port,..]
    @ivar methods: The contained methods for all ports.
    @type methods: [Method,..]
    """
    
    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.ports = []
        for p in root.getChildren('port'):
            port = Port(p, definitions, self)
            self.ports.append(port)
            
    def port(self, name):
        """
        Locate a port by name.
        @param name: A port name.
        @type name: str
        @return: The port object.
        @rtype: L{Port} 
        """
        for p in self.ports:
            if p.name == name:
                return p
        return None
    
    def setlocation(self, url, names=None):
        """
        Override the invocation location (url) for service method.
        @param url: A url location.
        @type url: A url.
        @param names:  A list of method names.  None=ALL
        @type names: [str,..]
        """
        for p in self.ports:
            for m in p.methods.values():
                if names is None or m.name in names:
                    m.location = url
        
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.
        Ports without soap bindings are discarded.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        filtered = []
        for p in self.ports:
            ref = qualify(p.binding, self.root, definitions.tns)
            binding = definitions.bindings.get(ref)
            if binding is None:
                raise Exception("binding '%s', not-found" % p.binding)
            if binding.soap is None:
                log.debug('binding "%s" - not a soap, discarded', binding.name)
                continue
            p.binding = binding
            filtered.append(p)
        self.ports = filtered
        
    def __gt__(self, other):
        return True


class Factory:
    """
    Simple WSDL object factory.
    @cvar tags: Dictionary of tag->constructor mappings.
    @type tags: dict
    """

    tags =\
    {
        'import' : Import, 
        'types' : Types, 
        'message' : Message, 
        'portType' : PortType,
        'binding' : Binding,
        'service' : Service,
    }
    
    @classmethod
    def create(cls, root, definitions):
        """
        Create an object based on the root tag name.
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        @return: The created object.
        @rtype: L{WObject} 
        """
        fn = cls.tags.get(root.name)
        if fn is not None:
            return fn(root, definitions)
        else:
            return None
