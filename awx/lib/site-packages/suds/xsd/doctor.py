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
The I{doctor} module provides classes for fixing broken (sick)
schema(s).
"""

from logging import getLogger
from suds.sax import splitPrefix, Namespace
from suds.sax.element import Element
from suds.plugin import DocumentPlugin, DocumentContext

log = getLogger(__name__)


class Doctor:
    """
    Schema Doctor.
    """
    def examine(self, root):
        """
        Examine and repair the schema (if necessary).
        @param root: A schema root element.
        @type root: L{Element}
        """
        pass


class Practice(Doctor):
    """
    A collection of doctors.
    @ivar doctors: A list of doctors.
    @type doctors: list
    """
    
    def __init__(self):
        self.doctors = []
        
    def add(self, doctor):
        """
        Add a doctor to the practice
        @param doctor: A doctor to add.
        @type doctor: L{Doctor}
        """
        self.doctors.append(doctor)

    def examine(self, root):
        for d in self.doctors:
            d.examine(root)
        return root


class TnsFilter:
    """
    Target Namespace filter.
    @ivar tns: A list of target namespaces.
    @type tns: [str,...]
    """

    def __init__(self, *tns):
        """
        @param tns: A list of target namespaces.
        @type tns: [str,...]
        """
        self.tns = []
        self.add(*tns)
        
    def add(self, *tns):
        """
        Add I{targetNamesapces} to be added.
        @param tns: A list of target namespaces.
        @type tns: [str,...]
        """
        self.tns += tns

    def match(self, root, ns):
        """
        Match by I{targetNamespace} excluding those that
        are equal to the specified namespace to prevent
        adding an import to itself.
        @param root: A schema root.
        @type root: L{Element}
        """
        tns = root.get('targetNamespace')
        if len(self.tns):
            matched = ( tns in self.tns )
        else:
            matched = 1
        itself = ( ns == tns )
        return ( matched and not itself )
    

class Import:
    """
    An <xs:import/> to be applied.
    @cvar xsdns: The XSD namespace.
    @type xsdns: (p,u)
    @ivar ns: An import namespace.
    @type ns: str
    @ivar location: An optional I{schemaLocation}.
    @type location: str
    @ivar filter: A filter used to restrict application to
        a particular schema.
    @type filter: L{TnsFilter}
    """

    xsdns = Namespace.xsdns
    
    def __init__(self, ns, location=None):
        """
        @param ns: An import namespace.
        @type ns: str
        @param location: An optional I{schemaLocation}.
        @type location: str
        """
        self.ns = ns
        self.location = location
        self.filter = TnsFilter()
        
    def setfilter(self, filter):
        """
        Set the filter.
        @param filter: A filter to set.
        @type filter: L{TnsFilter}
        """
        self.filter = filter
        
    def apply(self, root):
        """
        Apply the import (rule) to the specified schema.
        If the schema does not already contain an import for the
        I{namespace} specified here, it is added.
        @param root: A schema root.
        @type root: L{Element}
        """
        if not self.filter.match(root, self.ns):
            return
        if self.exists(root):
            return
        node = Element('import', ns=self.xsdns)
        node.set('namespace', self.ns)
        if self.location is not None:
            node.set('schemaLocation', self.location)
        log.debug('inserting: %s', node)
        root.insert(node)
        
    def add(self, root):
        """
        Add an <xs:import/> to the specified schema root.
        @param root: A schema root.
        @type root: L{Element}
        """
        node = Element('import', ns=self.xsdns)
        node.set('namespace', self.ns)
        if self.location is not None:
            node.set('schemaLocation', self.location)
        log.debug('%s inserted', node)
        root.insert(node) 
        
    def exists(self, root):
        """
        Check to see if the <xs:import/> already exists
        in the specified schema root by matching I{namesapce}.
        @param root: A schema root.
        @type root: L{Element}
        """
        for node in root.children:
            if node.name != 'import':
                continue
            ns = node.get('namespace')
            if self.ns == ns:
                return 1
        return 0
    

class ImportDoctor(Doctor, DocumentPlugin):
    """
    Doctor used to fix missing imports.
    @ivar imports: A list of imports to apply.
    @type imports: [L{Import},...]
    """

    def __init__(self, *imports):
        """
        """
        self.imports = []
        self.add(*imports)
        
    def add(self, *imports):
        """
        Add a namesapce to be checked.
        @param imports: A list of L{Import} objects.
        @type imports: [L{Import},..]
        """
        self.imports += imports
        
    def examine(self, node):
        for imp in self.imports:
            imp.apply(node)

    def parsed(self, context):
        node = context.document
        # xsd root
        if node.name == 'schema' and Namespace.xsd(node.namespace()):
            self.examine(node)
            return
        # look deeper
        context = DocumentContext()
        for child in node:
            context.document = child
            self.parsed(context)
        