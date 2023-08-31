User Authentication with Kerberos
==================================

.. index::
    pair: user authentication; Kerberos
    pair: Kerberos; Active Directory (AD)

User authentication via Active Directory (AD), also referred to as authentication through Kerberos, is supported through AWX.

To get started, first set up the Kerberos packages in AWX so that you can successfully generate a Kerberos ticket. To install the packages, use the following steps:

::

  yum install krb5-workstation
  yum install krb5-devel
  yum install krb5-libs

Once installed, edit the ``/etc/krb5.conf`` file, as follows, to provide the address of the AD, the domain, etc.:

::

  [logging]
   default = FILE:/var/log/krb5libs.log
   kdc = FILE:/var/log/krb5kdc.log
   admin_server = FILE:/var/log/kadmind.log

  [libdefaults]
   default_realm = WEBSITE.COM
   dns_lookup_realm = false
   dns_lookup_kdc = false
   ticket_lifetime = 24h
   renew_lifetime = 7d
   forwardable = true

  [realms]
   WEBSITE.COM = {
    kdc = WIN-SA2TXZOTVMV.website.com
    admin_server = WIN-SA2TXZOTVMV.website.com
   }

  [domain_realm]
   .website.com = WEBSITE.COM
   website.com = WEBSITE.COM

After the configuration file has been updated, you should be able to successfully authenticate and get a valid token.
The following steps show how to authenticate and get a token:

::

  [root@ip-172-31-26-180 ~]# kinit username
  Password for username@WEBSITE.COM:
  [root@ip-172-31-26-180 ~]#

  Check if we got a valid ticket.

  [root@ip-172-31-26-180 ~]# klist
  Ticket cache: FILE:/tmp/krb5cc_0
  Default principal: username@WEBSITE.COM

  Valid starting     Expires            Service principal
  01/25/16 11:42:56  01/25/16 21:42:53  krbtgt/WEBSITE.COM@WEBSITE.COM
    renew until 02/01/16 11:42:56
  [root@ip-172-31-26-180 ~]#

Once you have a valid ticket, you can check to ensure that everything is working as expected from command line. To test this, make sure that your inventory looks like the following:

::

  [windows]
  win01.WEBSITE.COM

  [windows:vars]
  ansible_user = username@WEBSITE.COM
  ansible_connection = winrm
  ansible_port = 5986

You should also:

- Ensure that the hostname is the proper client hostname matching the entry in AD and is not the IP address. 

- In the username declaration, ensure that the domain name (the text after ``@``) is properly entered with regard to upper- and lower-case letters, as Kerberos is case sensitive. For AWX, you should also ensure that the inventory looks the same.


.. note:: 

  If you encounter a ``Server not found in Kerberos database`` error message, and your inventory is configured using FQDNs (**not IP addresses**), ensure that the service principal name is not missing or mis-configured.


Now, running a playbook should run as expected. You can test this by running the playbook as the ``awx`` user.

Once you have verified that playbooks work properly, integration with AWX is easy. Generate the Kerberos ticket as the ``awx`` user and AWX should automatically pick up the generated ticket for authentication.

.. note::

  The python ``kerberos`` package must be installed. Ansible is designed to check if ``kerberos`` package is installed and, if so, it uses kerberos authentication.


AD and Kerberos Credentials
------------------------------

Active Directory only:

- If you are only planning to run playbooks against Windows machines with AD usernames and passwords as machine credentials, you can use "user@<domain>" format for the username and an associated password.

With Kerberos:

-  If Kerberos is installed, you can create a machine credential with the username and password, using the "user@<domain>" format for the username.


Working with Kerberos Tickets
-------------------------------

Ansible defaults to automatically managing Kerberos tickets when both the username and password are specified in the machine credential for a host that is configured for kerberos. A new ticket is created in a temporary credential cache for each host, before each task executes (to minimize the chance of ticket expiration). The temporary credential caches are deleted after each task, and will not interfere with the default credential cache.

To disable automatic ticket management (e.g., to use an existing SSO ticket or call ``kinit`` manually to populate the default credential cache), set ``ansible_winrm_kinit_mode=manual`` via the inventory.

Automatic ticket management requires a standard kinit binary on the control host system path. To specify a different location or binary name, set the ``ansible_winrm_kinit_cmd`` inventory variable to the fully-qualified path to an MIT krbv5 kinit-compatible binary.
