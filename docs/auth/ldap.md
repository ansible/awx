# LDAP
The Lightweight Directory Access Protocol (LDAP) is an open, vendor-neutral, industry standard application protocol for accessing and maintaining distributed directory information services over an Internet Protocol (IP) network. Directory services play an important role in developing intranet and Internet applications by allowing the sharing of information about users, systems, networks, services, and applications throughout the network.

# Configure LDAP Authentication
Please see the Tower documentation as well as Ansible blog posts for basic LDAP configuration. 

LDAP Authentication provides duplicate sets of configuration fields for authentication with up to six different LDAP servers. 
The default set of configuration fields take the form `AUTH_LDAP_<field name>`. Configuration fields for additional ldap servers are numbered `AUTH_LDAP_<n>_<field name>`.

## Test environment setup

Please see README.md of this repository: https://github.com/jangsutsr/deploy_ldap.git.
