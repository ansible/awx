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
Provides classes for handling soap multirefs.
"""

from logging import getLogger
from suds import *
from suds.sax.element import Element

log = getLogger(__name__)

soapenc = (None, 'http://schemas.xmlsoap.org/soap/encoding/')

class MultiRef:
    """
    Resolves and replaces multirefs.
    @ivar nodes: A list of non-multiref nodes.
    @type nodes: list
    @ivar catalog: A dictionary of multiref nodes by id.
    @type catalog: dict 
    """
    
    def __init__(self):
        self.nodes = []
        self.catalog = {}
    
    def process(self, body):
        """
        Process the specified soap envelope body and replace I{multiref} node
        references with the contents of the referenced node.
        @param body: A soap envelope body node.
        @type body: L{Element}
        @return: The processed I{body}
        @rtype: L{Element}
        """
        self.nodes = []
        self.catalog = {}
        self.build_catalog(body)
        self.update(body)
        body.children = self.nodes
        return body
    
    def update(self, node):
        """
        Update the specified I{node} by replacing the I{multiref} references with
        the contents of the referenced nodes and remove the I{href} attribute.
        @param node: A node to update.
        @type node: L{Element}
        @return: The updated node
        @rtype: L{Element}
        """
        self.replace_references(node)
        for c in node.children:
            self.update(c)
        return node
            
    def replace_references(self, node):
        """
        Replacing the I{multiref} references with the contents of the 
        referenced nodes and remove the I{href} attribute.  Warning:  since
        the I{ref} is not cloned, 
        @param node: A node to update.
        @type node: L{Element}
        """
        href = node.getAttribute('href')
        if href is None:
            return
        id = href.getValue()
        ref = self.catalog.get(id)
        if ref is None:
            log.error('soap multiref: %s, not-resolved', id)
            return
        node.append(ref.children)
        node.setText(ref.getText())
        for a in ref.attributes:
            if a.name != 'id':
                node.append(a)
        node.remove(href)
            
    def build_catalog(self, body):
        """
        Create the I{catalog} of multiref nodes by id and the list of
        non-multiref nodes.
        @param body: A soap envelope body node.
        @type body: L{Element}
        """
        for child in body.children:
            if self.soaproot(child):
                self.nodes.append(child)
            id = child.get('id')
            if id is None: continue
            key = '#%s' % id
            self.catalog[key] = child

    def soaproot(self, node):
        """
        Get whether the specified I{node} is a soap encoded root.
        This is determined by examining @soapenc:root='1'.
        The node is considered to be a root when the attribute
        is not specified.
        @param node: A node to evaluate.
        @type node: L{Element}
        @return: True if a soap encoded root.
        @rtype: bool
        """
        root = node.getAttribute('root', ns=soapenc)
        if root is None:
            return True
        else:
            return ( root.value == '1' )
        