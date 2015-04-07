#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import six

SP_SOAP_RESPONSE = six.b("""<S:Envelope
xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Header>
<paos:Request xmlns:paos="urn:liberty:paos:2003-08"
S:actor="http://schemas.xmlsoap.org/soap/actor/next"
S:mustUnderstand="1"
responseConsumerURL="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
service="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"/>
<ecp:Request xmlns:ecp="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"
IsPassive="0" S:actor="http://schemas.xmlsoap.org/soap/actor/next"
S:mustUnderstand="1">
<saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
https://openstack4.local/shibboleth
</saml:Issuer>
<samlp:IDPList xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol">
<samlp:IDPEntry ProviderID="https://idp.testshib.org/idp/shibboleth"/>
</samlp:IDPList></ecp:Request>
<ecp:RelayState xmlns:ecp="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"
S:actor="http://schemas.xmlsoap.org/soap/actor/next" S:mustUnderstand="1">
ss:mem:6f1f20fafbb38433467e9d477df67615</ecp:RelayState>
</S:Header><S:Body><samlp:AuthnRequest
xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
AssertionConsumerServiceURL="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
 ID="_a07186e3992e70e92c17b9d249495643" IssueInstant="2014-06-09T09:48:57Z"
 ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:PAOS" Version="2.0">
 <saml:Issuer
 xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
 https://openstack4.local/shibboleth
 </saml:Issuer><samlp:NameIDPolicy AllowCreate="1"/><samlp:Scoping>
 <samlp:IDPList>
 <samlp:IDPEntry ProviderID="https://idp.testshib.org/idp/shibboleth"/>
 </samlp:IDPList></samlp:Scoping></samlp:AuthnRequest></S:Body></S:Envelope>
""")


SAML2_ASSERTION = six.b("""<?xml version="1.0" encoding="UTF-8"?>
<soap11:Envelope xmlns:soap11="http://schemas.xmlsoap.org/soap/envelope/">
<soap11:Header>
<ecp:Response xmlns:ecp="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"
AssertionConsumerServiceURL="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
 soap11:actor="http://schemas.xmlsoap.org/soap/actor/next"
 soap11:mustUnderstand="1"/>
 <samlec:GeneratedKey xmlns:samlec="urn:ietf:params:xml:ns:samlec"
 soap11:actor="http://schemas.xmlsoap.org/soap/actor/next">
 x=
 </samlec:GeneratedKey>
 </soap11:Header>
 <soap11:Body>
 <saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"
Destination="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
ID="_bbbe6298d7ee586c915d952013875440"
InResponseTo="_a07186e3992e70e92c17b9d249495643"
IssueInstant="2014-06-09T09:48:58.945Z" Version="2.0">
<saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"
Format="urn:oasis:names:tc:SAML:2.0:nameid-format:entity">
https://idp.testshib.org/idp/shibboleth
</saml2:Issuer><saml2p:Status>
<saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
</saml2p:Status>
<saml2:EncryptedAssertion xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">
<xenc:EncryptedData xmlns:xenc="http://www.w3.org/2001/04/xmlenc#"
Id="_e5215ac77a6028a8da8caa8be89bad44"
Type="http://www.w3.org/2001/04/xmlenc#Element">
<xenc:EncryptionMethod Algorithm="http://www.w3.org/2001/04/xmlenc#aes128-cbc"
xmlns:xenc="http://www.w3.org/2001/04/xmlenc#"/>
<ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
<xenc:EncryptedKey Id="_204349856f6e73c9480afc949d1b4643"
xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<xenc:EncryptionMethod
Algorithm="http://www.w3.org/2001/04/xmlenc#rsa-oaep-mgf1p"
xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<ds:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"
xmlns:ds="http://www.w3.org/2000/09/xmldsig#"/>
</xenc:EncryptionMethod><ds:KeyInfo><ds:X509Data><ds:X509Certificate>
</ds:X509Certificate>
</ds:X509Data></ds:KeyInfo>
<xenc:CipherData xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<xenc:CipherValue>VALUE==</xenc:CipherValue></xenc:CipherData>
</xenc:EncryptedKey></ds:KeyInfo>
<xenc:CipherData xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<xenc:CipherValue>VALUE=</xenc:CipherValue></xenc:CipherData>
</xenc:EncryptedData></saml2:EncryptedAssertion></saml2p:Response>
</soap11:Body></soap11:Envelope>
""")

UNSCOPED_TOKEN_HEADER = 'UNSCOPED_TOKEN'

UNSCOPED_TOKEN = {
    "token": {
        "issued_at": "2014-06-09T09:48:59.643406Z",
        "extras": {},
        "methods": ["saml2"],
        "expires_at": "2014-06-09T10:48:59.643375Z",
        "user": {
            "OS-FEDERATION": {
                "identity_provider": {
                    "id": "testshib"
                },
                "protocol": {
                    "id": "saml2"
                },
                "groups": [
                    {"id": "1764fa5cf69a49a4918131de5ce4af9a"}
                ]
            },
            "id": "testhib%20user",
            "name": "testhib user"
        }
    }
}

PROJECTS = {
    "projects": [
        {
            "domain_id": "37ef61",
            "enabled": 'true',
            "id": "12d706",
            "links": {
                "self": "http://identity:35357/v3/projects/12d706"
            },
            "name": "a project name"
        },
        {
            "domain_id": "37ef61",
            "enabled": 'true',
            "id": "9ca0eb",
            "links": {
                "self": "http://identity:35357/v3/projects/9ca0eb"
            },
            "name": "another project"
        }
    ],
    "links": {
        "self": "http://identity:35357/v3/OS-FEDERATION/projects",
        "previous": 'null',
        "next": 'null'
    }
}

DOMAINS = {
    "domains": [
        {
            "description": "desc of domain",
            "enabled": 'true',
            "id": "37ef61",
            "links": {
                "self": "http://identity:35357/v3/domains/37ef61"
            },
            "name": "my domain"
        }
    ],
    "links": {
        "self": "http://identity:35357/v3/OS-FEDERATION/domains",
        "previous": 'null',
        "next": 'null'
    }
}
