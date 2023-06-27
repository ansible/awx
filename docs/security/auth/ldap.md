# LDAP
The Lightweight Directory Access Protocol (LDAP) is an open, vendor-neutral, industry-standard application protocol for accessing and maintaining distributed directory information services over an Internet Protocol (IP) network. Directory services play an important role in developing intranet and Internet applications by allowing the sharing of information about users, systems, networks, services, and applications throughout the network.


# Configure LDAP Authentication

Please see the [Tower documentation](https://docs.ansible.com/ansible-tower/latest/html/administration/ldap_auth.html) as well as [Ansible blog post](https://www.ansible.com/blog/getting-started-ldap-authentication-in-ansible-tower) for basic LDAP configuration.

LDAP Authentication provides duplicate sets of configuration fields for authentication with up to six different LDAP servers.
The default set of configuration fields take the form `AUTH_LDAP_<field name>`. Configuration fields for additional LDAP servers are numbered `AUTH_LDAP_<n>_<field name>`.


## Test Environment Setup

Please see `README.md` of this repository: https://github.com/ansible/deploy_ldap


# Basic Setup for FreeIPA

LDAP Server URI (append if you have multiple LDAPs)    
`ldaps://{{serverip1}}:636`

LDAP BIND DN (How to create a bind account in [FreeIPA](https://www.freeipa.org/page/Creating_a_binddn_for_Foreman)   
`uid=awx-bind,cn=sysaccounts,cn=etc,dc=example,dc=com`

LDAP BIND PASSWORD   
`{{yourbindaccountpassword}}`

LDAP USER DN TEMPLATE   
`uid=%(user)s,cn=users,cn=accounts,dc=example,dc=com`

LDAP GROUP TYPE   
`NestedMemberDNGroupType`

LDAP GROUP SEARCH
```
[
"cn=groups,cn=accounts,dc=example,dc=com",
"SCOPE_SUBTREE",
"(objectClass=groupOfNames)"
]
```

LDAP USER ATTRIBUTE MAP
```
{
"first_name": "givenName",
"last_name": "sn",
"email": "mail"
}
```

LDAP USER FLAGS BY GROUP
```
{
"is_superuser": "cn={{superusergroupname}},cn=groups,cn=accounts,dc=example,dc=com"
}
```

LDAP ORGANIZATION MAP
```
{
"{{yourorganizationname}}": {
"admins": "cn={{admingroupname}},cn=groups,cn=accounts,dc=example,dc=com",
"remove_admins": false
}
}
```
