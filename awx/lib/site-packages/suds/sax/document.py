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
Provides XML I{document} classes.
"""

from logging import getLogger
from suds import *
from suds.sax import *
from suds.sax.element import Element

log = getLogger(__name__)

class Document(Element):
    """ simple document """
    
    DECL = '<?xml version="1.0" encoding="UTF-8"?>'

    def __init__(self, root=None):
        Element.__init__(self, 'document')
        if root is not None:
            self.append(root)
        
    def root(self):
        if len(self.children):
            return self.children[0]
        else:
            return None
        
    def str(self):
        s = []
        s.append(self.DECL)
        s.append('\n')
        s.append(self.root().str())
        return ''.join(s)
    
    def plain(self):
        s = []
        s.append(self.DECL)
        s.append(self.root().plain())
        return ''.join(s)

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.str()