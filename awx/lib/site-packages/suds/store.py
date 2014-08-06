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
Contains XML text for documents to be distributed
with the suds lib.  Also, contains classes for accessing
these documents.
"""

from StringIO import StringIO
from logging import getLogger

log = getLogger(__name__)


#
# Soap section 5 encoding schema.
#
encoding = \
"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="http://schemas.xmlsoap.org/soap/encoding/" targetNamespace="http://schemas.xmlsoap.org/soap/encoding/">
        
 <xs:attribute name="root">
   <xs:annotation>
     <xs:documentation>
       'root' can be used to distinguish serialization roots from other
       elements that are present in a serialization but are not roots of
       a serialized value graph 
     </xs:documentation>
   </xs:annotation>
   <xs:simpleType>
     <xs:restriction base="xs:boolean">
       <xs:pattern value="0|1"/>
     </xs:restriction>
   </xs:simpleType>
 </xs:attribute>

  <xs:attributeGroup name="commonAttributes">
    <xs:annotation>
      <xs:documentation>
        Attributes common to all elements that function as accessors or 
        represent independent (multi-ref) values.  The href attribute is
        intended to be used in a manner like CONREF.  That is, the element
        content should be empty iff the href attribute appears
      </xs:documentation>
    </xs:annotation>
    <xs:attribute name="id" type="xs:ID"/>
    <xs:attribute name="href" type="xs:anyURI"/>
    <xs:anyAttribute namespace="##other" processContents="lax"/>
  </xs:attributeGroup>

  <!-- Global Attributes.  The following attributes are intended to be usable via qualified attribute names on any complex type referencing them. -->
       
  <!-- Array attributes. Needed to give the type and dimensions of an array's contents, and the offset for partially-transmitted arrays. -->
   
  <xs:simpleType name="arrayCoordinate">
    <xs:restriction base="xs:string"/>
  </xs:simpleType>
          
  <xs:attribute name="arrayType" type="xs:string"/>
  <xs:attribute name="offset" type="tns:arrayCoordinate"/>
  
  <xs:attributeGroup name="arrayAttributes">
    <xs:attribute ref="tns:arrayType"/>
    <xs:attribute ref="tns:offset"/>
  </xs:attributeGroup>    
  
  <xs:attribute name="position" type="tns:arrayCoordinate"/> 
  
  <xs:attributeGroup name="arrayMemberAttributes">
    <xs:attribute ref="tns:position"/>
  </xs:attributeGroup>    

  <xs:group name="Array">
    <xs:sequence>
      <xs:any namespace="##any" minOccurs="0" maxOccurs="unbounded" processContents="lax"/>
    </xs:sequence>
  </xs:group>

  <xs:element name="Array" type="tns:Array"/>
  <xs:complexType name="Array">
    <xs:annotation>
      <xs:documentation>
       'Array' is a complex type for accessors identified by position 
      </xs:documentation>
    </xs:annotation>
    <xs:group ref="tns:Array" minOccurs="0"/>
    <xs:attributeGroup ref="tns:arrayAttributes"/>
    <xs:attributeGroup ref="tns:commonAttributes"/>
  </xs:complexType> 

  <!-- 'Struct' is a complex type for accessors identified by name. 
       Constraint: No element may be have the same name as any other,
       nor may any element have a maxOccurs > 1. -->
   
  <xs:element name="Struct" type="tns:Struct"/>

  <xs:group name="Struct">
    <xs:sequence>
      <xs:any namespace="##any" minOccurs="0" maxOccurs="unbounded" processContents="lax"/>
    </xs:sequence>
  </xs:group>

  <xs:complexType name="Struct">
    <xs:group ref="tns:Struct" minOccurs="0"/>
    <xs:attributeGroup ref="tns:commonAttributes"/>
  </xs:complexType> 

  <!-- 'Base64' can be used to serialize binary data using base64 encoding
       as defined in RFC2045 but without the MIME line length limitation. -->

  <xs:simpleType name="base64">
    <xs:restriction base="xs:base64Binary"/>
  </xs:simpleType>

 <!-- Element declarations corresponding to each of the simple types in the 
      XML Schemas Specification. -->

  <xs:element name="duration" type="tns:duration"/>
  <xs:complexType name="duration">
    <xs:simpleContent>
      <xs:extension base="xs:duration">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="dateTime" type="tns:dateTime"/>
  <xs:complexType name="dateTime">
    <xs:simpleContent>
      <xs:extension base="xs:dateTime">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>



  <xs:element name="NOTATION" type="tns:NOTATION"/>
  <xs:complexType name="NOTATION">
    <xs:simpleContent>
      <xs:extension base="xs:QName">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  

  <xs:element name="time" type="tns:time"/>
  <xs:complexType name="time">
    <xs:simpleContent>
      <xs:extension base="xs:time">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="date" type="tns:date"/>
  <xs:complexType name="date">
    <xs:simpleContent>
      <xs:extension base="xs:date">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="gYearMonth" type="tns:gYearMonth"/>
  <xs:complexType name="gYearMonth">
    <xs:simpleContent>
      <xs:extension base="xs:gYearMonth">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="gYear" type="tns:gYear"/>
  <xs:complexType name="gYear">
    <xs:simpleContent>
      <xs:extension base="xs:gYear">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="gMonthDay" type="tns:gMonthDay"/>
  <xs:complexType name="gMonthDay">
    <xs:simpleContent>
      <xs:extension base="xs:gMonthDay">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="gDay" type="tns:gDay"/>
  <xs:complexType name="gDay">
    <xs:simpleContent>
      <xs:extension base="xs:gDay">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="gMonth" type="tns:gMonth"/>
  <xs:complexType name="gMonth">
    <xs:simpleContent>
      <xs:extension base="xs:gMonth">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  
  <xs:element name="boolean" type="tns:boolean"/>
  <xs:complexType name="boolean">
    <xs:simpleContent>
      <xs:extension base="xs:boolean">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="base64Binary" type="tns:base64Binary"/>
  <xs:complexType name="base64Binary">
    <xs:simpleContent>
      <xs:extension base="xs:base64Binary">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="hexBinary" type="tns:hexBinary"/>
  <xs:complexType name="hexBinary">
    <xs:simpleContent>
     <xs:extension base="xs:hexBinary">
       <xs:attributeGroup ref="tns:commonAttributes"/>
     </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="float" type="tns:float"/>
  <xs:complexType name="float">
    <xs:simpleContent>
      <xs:extension base="xs:float">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="double" type="tns:double"/>
  <xs:complexType name="double">
    <xs:simpleContent>
      <xs:extension base="xs:double">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="anyURI" type="tns:anyURI"/>
  <xs:complexType name="anyURI">
    <xs:simpleContent>
      <xs:extension base="xs:anyURI">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="QName" type="tns:QName"/>
  <xs:complexType name="QName">
    <xs:simpleContent>
      <xs:extension base="xs:QName">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  
  <xs:element name="string" type="tns:string"/>
  <xs:complexType name="string">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="normalizedString" type="tns:normalizedString"/>
  <xs:complexType name="normalizedString">
    <xs:simpleContent>
      <xs:extension base="xs:normalizedString">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="token" type="tns:token"/>
  <xs:complexType name="token">
    <xs:simpleContent>
      <xs:extension base="xs:token">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="language" type="tns:language"/>
  <xs:complexType name="language">
    <xs:simpleContent>
      <xs:extension base="xs:language">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="Name" type="tns:Name"/>
  <xs:complexType name="Name">
    <xs:simpleContent>
      <xs:extension base="xs:Name">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="NMTOKEN" type="tns:NMTOKEN"/>
  <xs:complexType name="NMTOKEN">
    <xs:simpleContent>
      <xs:extension base="xs:NMTOKEN">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="NCName" type="tns:NCName"/>
  <xs:complexType name="NCName">
    <xs:simpleContent>
      <xs:extension base="xs:NCName">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="NMTOKENS" type="tns:NMTOKENS"/>
  <xs:complexType name="NMTOKENS">
    <xs:simpleContent>
      <xs:extension base="xs:NMTOKENS">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="ID" type="tns:ID"/>
  <xs:complexType name="ID">
    <xs:simpleContent>
      <xs:extension base="xs:ID">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="IDREF" type="tns:IDREF"/>
  <xs:complexType name="IDREF">
    <xs:simpleContent>
      <xs:extension base="xs:IDREF">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="ENTITY" type="tns:ENTITY"/>
  <xs:complexType name="ENTITY">
    <xs:simpleContent>
      <xs:extension base="xs:ENTITY">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="IDREFS" type="tns:IDREFS"/>
  <xs:complexType name="IDREFS">
    <xs:simpleContent>
      <xs:extension base="xs:IDREFS">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="ENTITIES" type="tns:ENTITIES"/>
  <xs:complexType name="ENTITIES">
    <xs:simpleContent>
      <xs:extension base="xs:ENTITIES">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="decimal" type="tns:decimal"/>
  <xs:complexType name="decimal">
    <xs:simpleContent>
      <xs:extension base="xs:decimal">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="integer" type="tns:integer"/>
  <xs:complexType name="integer">
    <xs:simpleContent>
      <xs:extension base="xs:integer">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="nonPositiveInteger" type="tns:nonPositiveInteger"/>
  <xs:complexType name="nonPositiveInteger">
    <xs:simpleContent>
      <xs:extension base="xs:nonPositiveInteger">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="negativeInteger" type="tns:negativeInteger"/>
  <xs:complexType name="negativeInteger">
    <xs:simpleContent>
      <xs:extension base="xs:negativeInteger">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="long" type="tns:long"/>
  <xs:complexType name="long">
    <xs:simpleContent>
      <xs:extension base="xs:long">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="int" type="tns:int"/>
  <xs:complexType name="int">
    <xs:simpleContent>
      <xs:extension base="xs:int">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="short" type="tns:short"/>
  <xs:complexType name="short">
    <xs:simpleContent>
      <xs:extension base="xs:short">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="byte" type="tns:byte"/>
  <xs:complexType name="byte">
    <xs:simpleContent>
      <xs:extension base="xs:byte">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="nonNegativeInteger" type="tns:nonNegativeInteger"/>
  <xs:complexType name="nonNegativeInteger">
    <xs:simpleContent>
      <xs:extension base="xs:nonNegativeInteger">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="unsignedLong" type="tns:unsignedLong"/>
  <xs:complexType name="unsignedLong">
    <xs:simpleContent>
      <xs:extension base="xs:unsignedLong">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="unsignedInt" type="tns:unsignedInt"/>
  <xs:complexType name="unsignedInt">
    <xs:simpleContent>
      <xs:extension base="xs:unsignedInt">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="unsignedShort" type="tns:unsignedShort"/>
  <xs:complexType name="unsignedShort">
    <xs:simpleContent>
      <xs:extension base="xs:unsignedShort">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="unsignedByte" type="tns:unsignedByte"/>
  <xs:complexType name="unsignedByte">
    <xs:simpleContent>
      <xs:extension base="xs:unsignedByte">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="positiveInteger" type="tns:positiveInteger"/>
  <xs:complexType name="positiveInteger">
    <xs:simpleContent>
      <xs:extension base="xs:positiveInteger">
        <xs:attributeGroup ref="tns:commonAttributes"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>

  <xs:element name="anyType"/>
</xs:schema>
"""


class DocumentStore:
    """
    The I{suds} document store provides a local repository
    for xml documnts.
    @cvar protocol: The URL protocol for the store.
    @type protocol: str
    @cvar store: The mapping of URL location to documents.
    @type store: dict
    """
    
    protocol = 'suds'
    
    store = {
        'schemas.xmlsoap.org/soap/encoding/' : encoding
    }
    
    def open(self, url):
        """
        Open a document at the specified url.
        @param url: A document URL.
        @type url: str
        @return: A file pointer to the document.
        @rtype: StringIO
        """
        protocol, location = self.split(url)
        if protocol == self.protocol:
            return self.find(location)
        else:
            return None
        
    def find(self, location):
        """
        Find the specified location in the store.
        @param location: The I{location} part of a URL.
        @type location: str
        @return: An input stream to the document.
        @rtype: StringIO
        """
        try:
            content = self.store[location]
            return StringIO(content)
        except:
            reason = 'location "%s" not in document store' % location
            raise Exception, reason
        
    def split(self, url):
        """
        Split the url into I{protocol} and I{location}
        @param url: A URL.
        @param url: str
        @return: (I{url}, I{location})
        @rtype: tuple
        """
        parts = url.split('://', 1)
        if len(parts) == 2:
            return parts
        else:
            return (None, url)