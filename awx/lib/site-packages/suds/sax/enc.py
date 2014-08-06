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
Provides XML I{special character} encoder classes.
"""

import re

class Encoder:
    """
    An XML special character encoder/decoder.
    @cvar encodings: A mapping of special characters encoding.
    @type encodings: [(str,str)]
    @cvar decodings: A mapping of special characters decoding.
    @type decodings: [(str,str)]
    @cvar special: A list of special characters
    @type special: [char]
    """
    
    encodings = \
        (( '&(?!(amp|lt|gt|quot|apos);)', '&amp;' ),( '<', '&lt;' ),( '>', '&gt;' ),( '"', '&quot;' ),("'", '&apos;' ))
    decodings = \
        (( '&lt;', '<' ),( '&gt;', '>' ),( '&quot;', '"' ),( '&apos;', "'" ),( '&amp;', '&' ))
    special = \
        ('&', '<', '>', '"', "'")
    
    def needsEncoding(self, s):
        """
        Get whether string I{s} contains special characters.
        @param s: A string to check.
        @type s: str
        @return: True if needs encoding.
        @rtype: boolean
        """
        if isinstance(s, basestring):
            for c in self.special:
                if c in s:
                    return True
        return False
    
    def encode(self, s):
        """
        Encode special characters found in string I{s}.
        @param s: A string to encode.
        @type s: str
        @return: The encoded string.
        @rtype: str
        """
        if isinstance(s, basestring) and self.needsEncoding(s):
            for x in self.encodings:
                s = re.sub(x[0], x[1], s)
        return s
    
    def decode(self, s):
        """
        Decode special characters encodings found in string I{s}.
        @param s: A string to decode.
        @type s: str
        @return: The decoded string.
        @rtype: str
        """
        if isinstance(s, basestring) and '&' in s:
            for x in self.decodings:
                s = s.replace(x[0], x[1])
        return s
