
.. _ag_secret_handling:

Secret handling and connection security 
=======================================


This document describes how |RHAT| handles secrets and
connections in a secure fashion.

Secret Handling
---------------

|At| manages three sets of secrets:

-  user passwords for local |at| users

-  secrets for |at| operational use (database password, message
   bus password, etc.)

-  secrets for automation use (SSH keys, cloud credentials, external
   password vault credentials, etc.)

User passwords for local users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|At| hashes local |at| user passwords with the PBKDF2
algorithm using a SHA256 hash. Users who authenticate via external
account mechanisms (LDAP, SAML, OAuth, and others) do not have any
password or secret stored.

Secret handling for operational use
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index:: 
   single: keys
   pair: secret key; handling
   pair: secret key; regenerate


|At| contains the following secrets used operationally:

-  ``/etc/tower/SECRET_KEY``

   -  A secret key used for encrypting automation secrets in the
      database (see below). If the ``SECRET_KEY`` changes or is unknown,
      no encrypted fields in the database will be accessible.

-  ``/etc/tower/tower.{cert,key}``

   -  SSL certificate and key for the |at| web service. A
      self-signed cert/key is installed by default; the customer can
      provide a locally appropriate certificate and key.

-  Database password in ``/etc/tower/conf.d/postgres.py`` and message bus
   password in ``/etc/tower/conf.d/channels.py``

   -  Passwords for connecting to |at| component services

These secrets are all stored unencrypted on the |at| server, as
they are all needed to be read by the |at| service at startup
in an automated fashion. All secrets are protected by Unix permissions,
and restricted to root and the |at| service user awx.

If hiding of these secrets is required, the files that these secrets are read from are interpreted Python. These files can be adjusted to retrieve these secrets via some other mechanism anytime a service restarts.

.. note::

    If the secrets system is down, the controller will be unable to get the information and may fail in a way that would be recoverable once the service is restored. Using some redundancy on that system is highly recommended.


If, for any reason you believe the ``SECRET_KEY`` the controller generated for you has been compromised and needs to be regenerated, you can run a tool from the installer that behaves much like the controller backup and restore tool.

To generate a new secret key, run ``setup.sh -k`` using the inventory from your install.

A backup copy of the prior key is saved in ``/etc/tower/``.


Secret handling for automation use
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|At| stores a variety of secrets in the database that are
either used for automation or are a result of automation. These secrets
include:

-  all secret fields of all credential types (passwords, secret keys,
   authentication tokens, secret cloud credentials)

-  secret tokens and passwords for external services defined in |at| settings

-  “password” type survey fields entries

To encrypt secret fields, the controller uses AES in CBC mode with a 256-bit key
for encryption, PKCS7 padding, and HMAC using SHA256 for authentication.
The encryption/decryption process derives the AES-256 bit encryption key
from the ``SECRET_KEY`` (described above), the field name of the model field
and the database assigned auto-incremented record ID. Thus, if any
attribute used in the key generation process changes, the controller fails to
correctly decrypt the secret. |at| is designed such that the
``SECRET_KEY`` is never readable in playbooks |at| launches, that
these secrets are never readable by the controller users, and no secret field values
are ever made available via the |at| REST API. If a secret value is
used in a playbook, we recommend using ``no_log`` on the task so that
it is not accidentally logged.


Connection Security
-------------------

Internal Services
~~~~~~~~~~~~~~~~~

|At| connects to the following services as part of internal
operation:

-  PostgreSQL database

-  A Redis key/value store

The connection to redis is over a local unix socket,
restricted to the awx service user.

The connection to the PostgreSQL database is done via password
authentication over TCP, either via localhost or remotely (external
database). This connection can use PostgreSQL’s built in support for
SSL/TLS, as natively configured by the installer support.
SSL/TLS protocols are configured by the default OpenSSL
configuration.

External Access
~~~~~~~~~~~~~~~

|At| is accessed via standard HTTP/HTTPS on standard ports,
provided by nginx. A self-signed cert/key is installed by default; the
customer can provide a locally appropriate certificate and key. SSL/TLS
algorithm support is configured in the /etc/nginx/nginx.conf
configuration file. An “intermediate” profile is used by default, and
can be configured by the customer. Customer changes must be reapplied on
each update.

Managed Nodes
~~~~~~~~~~~~~

|AT| also connects to managed machines and services as part of
automation. All connections to managed machines are done via standard
secure mechanism as specified such as SSH, WinRM, SSL/TLS, and so on -
each of these inherits configuration from the system configuration for
the feature in question (such as the system OpenSSL configuration).
