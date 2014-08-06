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
The I{wsse} module provides WS-Security.
"""

from logging import getLogger
from suds import *
from suds.sudsobject import Object
from suds.sax.element import Element
from suds.sax.date import UTC
from datetime import datetime, timedelta

try:
    from hashlib import md5
except ImportError:
    # Python 2.4 compatibility
    from md5 import md5


dsns = \
    ('ds',
     'http://www.w3.org/2000/09/xmldsig#')
wssens = \
    ('wsse', 
     'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd')
wsuns = \
    ('wsu',
     'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd')
wsencns = \
    ('wsenc',
     'http://www.w3.org/2001/04/xmlenc#')


class Security(Object):
    """
    WS-Security object.
    @ivar tokens: A list of security tokens
    @type tokens: [L{Token},...]
    @ivar signatures: A list of signatures.
    @type signatures: TBD
    @ivar references: A list of references.
    @type references: TBD
    @ivar keys: A list of encryption keys.
    @type keys: TBD
    """
    
    def __init__(self):
        """ """
        Object.__init__(self)
        self.mustUnderstand = True
        self.tokens = []
        self.signatures = []
        self.references = []
        self.keys = []
        
    def xml(self):
        """
        Get xml representation of the object.
        @return: The root node.
        @rtype: L{Element}
        """
        root = Element('Security', ns=wssens)
        root.set('mustUnderstand', str(self.mustUnderstand).lower())
        for t in self.tokens:
            root.append(t.xml())
        return root


class Token(Object):
    """ I{Abstract} security token. """
    
    @classmethod
    def now(cls):
        return datetime.now()
    
    @classmethod
    def utc(cls):
        return datetime.utcnow()
    
    @classmethod
    def sysdate(cls):
        utc = UTC()
        return str(utc)
    
    def __init__(self):
            Object.__init__(self)


class UsernameToken(Token):
    """
    Represents a basic I{UsernameToken} WS-Secuirty token.
    @ivar username: A username.
    @type username: str
    @ivar password: A password.
    @type password: str
    @ivar nonce: A set of bytes to prevent reply attacks.
    @type nonce: str
    @ivar created: The token created.
    @type created: L{datetime}
    """

    def __init__(self, username=None, password=None):
        """
        @param username: A username.
        @type username: str
        @param password: A password.
        @type password: str
        """
        Token.__init__(self)
        self.username = username
        self.password = password
        self.nonce = None
        self.created = None
        
    def setnonce(self, text=None):
        """
        Set I{nonce} which is arbitraty set of bytes to prevent
        reply attacks.
        @param text: The nonce text value.
            Generated when I{None}.
        @type text: str
        """
        if text is None:
            s = []
            s.append(self.username)
            s.append(self.password)
            s.append(Token.sysdate())
            m = md5()
            m.update(':'.join(s))
            self.nonce = m.hexdigest()
        else:
            self.nonce = text
        
    def setcreated(self, dt=None):
        """
        Set I{created}.
        @param dt: The created date & time.
            Set as datetime.utc() when I{None}.
        @type dt: L{datetime}
        """
        if dt is None:
            self.created = Token.utc()
        else:
            self.created = dt
        
        
    def xml(self):
        """
        Get xml representation of the object.
        @return: The root node.
        @rtype: L{Element}
        """
        root = Element('UsernameToken', ns=wssens)
        u = Element('Username', ns=wssens)
        u.setText(self.username)
        root.append(u)
        p = Element('Password', ns=wssens)
        p.setText(self.password)
        root.append(p)
        if self.nonce is not None:
            n = Element('Nonce', ns=wssens)
            n.setText(self.nonce)
            root.append(n)
        if self.created is not None:
            n = Element('Created', ns=wsuns)
            n.setText(str(UTC(self.created)))
            root.append(n)
        return root


class Timestamp(Token):
    """
    Represents the I{Timestamp} WS-Secuirty token.
    @ivar created: The token created.
    @type created: L{datetime}
    @ivar expires: The token expires.
    @type expires: L{datetime}
    """

    def __init__(self, validity=90):
        """
        @param validity: The time in seconds.
        @type validity: int
        """
        Token.__init__(self)
        self.created = Token.utc()
        self.expires = self.created + timedelta(seconds=validity)
        
    def xml(self):
        root = Element("Timestamp", ns=wsuns)
        created = Element('Created', ns=wsuns)
        created.setText(str(UTC(self.created)))
        expires = Element('Expires', ns=wsuns)
        expires.setText(str(UTC(self.expires)))
        root.append(created)
        root.append(expires)
        return root