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
Provides modules containing classes to support
marshalling (XML).
"""

from suds.sudsobject import Object


class Content(Object):
    """
    Marshaller Content.
    @ivar tag: The content tag.
    @type tag: str
    @ivar value: The content's value.
    @type value: I{any}
    """
    
    extensions = []
    
    def __init__(self, tag=None, value=None, **kwargs):
        """
        @param tag: The content tag.
        @type tag: str
        @param value: The content's value.
        @type value: I{any}
        """
        Object.__init__(self)
        self.tag = tag
        self.value = value
        for k,v in kwargs.items():
            setattr(self, k, v)
            
    def __getattr__(self, name):
        if name not in self.__dict__:
            if name in self.extensions:
                v = None
                setattr(self, name, v)
            else:
                raise AttributeError, \
                    'Content has no attribute %s' % name
        else:
            v = self.__dict__[name]
        return v