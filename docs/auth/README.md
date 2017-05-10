This folder describes third-party authentications supported by Ansible Tower. These authentications can be configured and enabled inside Tower.

When a user wants to log into Tower, she can explicitly choose some of the supported authentications to log in instead of Tower's own authentication using username and password. Here is a list of such authentications:
* Google OAuth2
* Github OAuth2
* Github Organization OAuth2
* Github Team OAuth2
* Microsoft Azure Active Directory (AD) OAuth2

On the other hand, the rest of authentication methods use the same types of login info as Tower(username and password), but authenticate using external auth systems rather than Tower's own database. If some of these methods are enabled, Tower will try authenticating using the enabled methods *before Tower's own authentication method*. In specific, it follows the order
* LDAP
* RADIUS
* TACACS+
* SAML

Tower will try authenticating against each enabled authentication method *in the specified order*, meaning if the same username and password is valid in multiple enabled auth methods (For example, both LDAP and TACACS+), Tower will only use the first positive match (In the above example, log a user in via LDAP and skip TACACS+).

## Notes:
* TACACS+/RADIUS users and normal Tower users are strictly separated. For example, suppose there is a TACACS+ user with username 'Alice' which is known to TACACS+ backend but not Tower. If a user record with the same username 'Alice' is created in Tower before any log in attempt, Tower will always use its own authentication backend to authenticate Alice, even if TACACS+ backend is also available. On the other hand, if a successful log in attempt is conducted before any explicit user creation in Tower, a TACACS+ user 'Alice' is automatically created and Tower will always use TACACS+ backend for authenticating 'Alice'.
