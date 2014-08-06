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
Provides classes for the (WS) SOAP I{document/literal}.
"""

from logging import getLogger
from suds import *
from suds.bindings.binding import Binding
from suds.sax.element import Element

log = getLogger(__name__)


class Document(Binding):
    """
    The document/literal style.  Literal is the only (@use) supported
    since document/encoded is pretty much dead.
    Although the soap specification supports multiple documents within the soap
    <body/>, it is very uncommon.  As such, suds presents an I{RPC} view of
    service methods defined with a single document parameter.  This is done so 
    that the user can pass individual parameters instead of one, single document.
    To support the complete specification, service methods defined with multiple documents
    (multiple message parts), must present a I{document} view for that method.
    """
        
    def bodycontent(self, method, args, kwargs):
        #
        # The I{wrapped} vs I{bare} style is detected in 2 ways.
        # If there is 2+ parts in the message then it is I{bare}.
        # If there is only (1) part and that part resolves to a builtin then
        # it is I{bare}.  Otherwise, it is I{wrapped}.
        #
        if not len(method.soap.input.body.parts):
            return ()
        wrapped = method.soap.input.body.wrapped
        if wrapped:
            pts = self.bodypart_types(method)
            root = self.document(pts[0])
        else:
            root = []
        n = 0
        for pd in self.param_defs(method):
            if n < len(args):
                value = args[n]
            else:
                value = kwargs.get(pd[0])
            n += 1
            p = self.mkparam(method, pd, value)
            if p is None:
                continue
            if not wrapped:
                ns = pd[1].namespace('ns0')
                p.setPrefix(ns[0], ns[1])
            root.append(p)
        return root

    def replycontent(self, method, body):
        wrapped = method.soap.output.body.wrapped
        if wrapped:
            return body[0].children
        else:
            return body.children
        
    def document(self, wrapper):
        """
        Get the document root.  For I{document/literal}, this is the
        name of the wrapper element qualifed by the schema tns.
        @param wrapper: The method name.
        @type wrapper: L{xsd.sxbase.SchemaObject}
        @return: A root element.
        @rtype: L{Element}
        """
        tag = wrapper[1].name
        ns = wrapper[1].namespace('ns0')
        d = Element(tag, ns=ns)
        return d
    
    def mkparam(self, method, pdef, object):
        #
        # Expand list parameters into individual parameters
        # each with the type information.  This is because in document
        # arrays are simply unbounded elements.
        #
        if isinstance(object, (list, tuple)):
            tags = []
            for item in object:
                tags.append(self.mkparam(method, pdef, item))
            return tags
        else:
            return Binding.mkparam(self, method, pdef, object)
        
    def param_defs(self, method):
        #
        # Get parameter definitions for document literal.
        # The I{wrapped} vs I{bare} style is detected in 2 ways.
        # If there is 2+ parts in the message then it is I{bare}.
        # If there is only (1) part and that part resolves to a builtin then
        # it is I{bare}.  Otherwise, it is I{wrapped}.
        #
        pts = self.bodypart_types(method)
        wrapped = method.soap.input.body.wrapped
        if not wrapped:
            return pts
        result = []
        # wrapped
        for p in pts:
            resolved = p[1].resolve()
            for child, ancestry in resolved:
                if child.isattr():
                    continue
                if self.bychoice(ancestry):
                    log.debug(
                        '%s\ncontained by <choice/>, excluded as param for %s()',
                        child,
                        method.name)
                    continue
                result.append((child.name, child))
        return result
    
    def returned_types(self, method):
        result = []
        wrapped = method.soap.output.body.wrapped
        rts = self.bodypart_types(method, input=False)
        if wrapped:
            for pt in rts:
                resolved = pt.resolve(nobuiltin=True)
                for child, ancestry in resolved:
                    result.append(child)
                break
        else:
            result += rts
        return result
    
    def bychoice(self, ancestry):
        """
        The ancestry contains a <choice/>
        @param ancestry: A list of ancestors.
        @type ancestry: list
        @return: True if contains <choice/>
        @rtype: boolean
        """
        for x in ancestry:
            if x.choice():
                return True
        return False