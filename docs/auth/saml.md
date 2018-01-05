# SAML
Security Assertion Markup Language, or SAML, is an open standard for exchanging authentication and/or authorization data between an identity provider (i.e. LDAP) and a service provider (i.e. AWX). More concretely, AWX can be configured to talk with SAML in order to authenticate (create/login/logout) users of AWX. User Team and Organization membership can be embedded in the SAML response to AWX. 

# Configure SAML Authentication
Please see the Tower documentation as well as Ansible blog posts for basic SAML configuration.

# Configure SAML for Team and Organization Membership
AWX can be configured to look for particular attributes that contain AWX Team and Organization membership to associate with users when the login to AWX. The attribute names are defined in AWX settings. Specifically, the authentication settings tab and SAML sub category fields *SAML Team Map* and *SAML Organization Attribute Mapping*. The meaning and usefulness of these settings is best motivated through example.

**Example SAML Organization Attribute Mapping**
Below is an example SAML attribute that embeds user organization membership in the attribute *member-of*.
```
<saml2:AttributeStatement> 
    <saml2:Attribute FriendlyName="member-of" Name="member-of" NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:unspecified">
   	 <saml2:AttributeValue>Engineering</saml2:AttributeValue>
   	 <saml2:AttributeValue>IT</saml2:AttributeValue>
   	 <saml2:AttributeValue>HR</saml2:AttributeValue>
   	 <saml2:AttributeValue>Sales</saml2:AttributeValue>
    </saml2:Attribute>
</saml2:AttributeStatement> 
```
Below, the corresponding AWX configuration.
```
{
  "saml_attr": "member-of",
  "remove": true
}
```
**saml_attr:** The saml attribute name where the organization array can be found.
**remove:** True to remove user from all organizations before adding the user to the list of Organizations. False to keep the user in whatever Organization(s) they are in while adding the user to the Organization(s) in the SAML attribute.

**Example SAML Team Map**
Below is another example of a SAML attribute that contains a Team membership in a list.
```
  <saml:AttributeStatement>
     <saml:Attribute
       xmlns:x500="urn:oasis:names:tc:SAML:2.0:profiles:attribute:X500"
       x500:Encoding="LDAP"
       NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri"
       Name="urn:oid:1.3.6.1.4.1.5923.1.1.1.1"
       FriendlyName="eduPersonAffiliation">
       <saml:AttributeValue
         xsi:type="xs:string">member</saml:AttributeValue>
       <saml:AttributeValue
         xsi:type="xs:string">staff</saml:AttributeValue>
     </saml:Attribute>
   </saml:AttributeStatement>
```

```
{
  "saml_attr": "eduPersonAffiliation",
  "remove": true,
  "team_org_map": [
    {
      "team": "Blue",
      "organization": "Default1"
    },
    {
      "team": "Blue",
      "organization": "Default2"
    },
    {
      "team": "Blue",
      "organization": "Default3"
    },
    {
      "team": "Red",
      "organization": "Default1"
    },
    {
      "team": "Green",
      "organization": "Default1"
    },
    {
      "team": "Green",
      "organization": "Default3"
    }
  ]
}
```
**saml_attr:** The saml attribute name where the team array can be found.
**remove:** True to remove user from all Teams before adding the user to the list of Teams. False to keep the user in whatever Team(s) they are in while adding the user to the Team(s) in the SAML attribute.
**team_org_map:** An array of dictionaries of the form `{ "team": "<AWX Team Name>", "organization": "<AWX Org Name>" }` that defines mapping from AWX Team -> AWX Organization. This is needed because the same named Team can exist in multiple Organizations in Tower. The organization to which a team listed in a SAML attribute belongs to would be ambiguous without this mapping.

