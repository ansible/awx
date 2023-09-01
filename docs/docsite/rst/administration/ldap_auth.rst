.. _ag_auth_ldap:

Setting up LDAP Authentication
================================

.. index:: 
   single: LDAP
   pair: authentication; LDAP
   

.. note::

  If the LDAP server you want to connect to has a certificate that is self-signed or signed by a corporate internal certificate authority (CA), the CA certificate must be added to the system's trusted CAs. Otherwise, connection to the LDAP server will result in an error that the certificate issuer is not recognized.

Administrators use LDAP as a source for account authentication information for AWX users. User authentication is provided, but not the synchronization of user permissions and credentials. Organization membership (as well as the organization admin) and team memberships can be synchronized.

When so configured, a user who logs in with an LDAP username and password automatically gets an AWX account created for them and they can be automatically placed into organizations as either regular users or organization administrators.

Users created via an LDAP login cannot change their username, first name, last name, or set a local password for themselves. This is also tunable to restrict editing of other field names.

To configure LDAP integration for AWX:

1. First, create a user in LDAP that has access to read the entire LDAP structure.

2. Test if you can make successful queries to the LDAP server, use the ``ldapsearch`` command, which is a command line tool that can be installed on AWX command line as well as on other Linux and OSX systems. Use the following command to query the ldap server, where *josie* and *Josie4Cloud* are replaced by attributes that work for your setup:

::

  ldapsearch -x  -H ldap://win -D "CN=josie,CN=Users,DC=website,DC=com" -b "dc=website,dc=com" -w Josie4Cloud

Here ``CN=josie,CN=users,DC=website,DC=com`` is the Distinguished Name of the connecting user.

.. note::

  The ``ldapsearch`` utility is not automatically pre-installed with AWX, however, you can install it from the ``openldap-clients`` package.

3. In the AWX User Interface, click **Settings** from the left navigation and click to select **LDAP settings** from the list of Authentication options. 


  Multiple LDAP configurations are not needed per LDAP server, but you can configure multiple LDAP servers from this page, otherwise, leave the server at **Default**:

  .. image:: ../common/images/configure-awx-auth-ldap-servers.png

  |

  The equivalent API endpoints will show ``AUTH_LDAP_*`` repeated: ``AUTH_LDAP_1_*``, ``AUTH_LDAP_2_*``, ..., ``AUTH_LDAP_5_*`` to denote server designations.


4. To enter or modify the LDAP server address to connect to, click **Edit** and enter  in the **LDAP Server URI** field using the same format as the one prepopulated in the text field:

.. image:: ../common/images/configure-awx-auth-ldap-server-uri.png

.. note::

  Multiple LDAP servers may be specified by separating each with spaces or commas. Click the |help| icon to comply with proper syntax and rules.

.. |help| image:: ../common/images/tooltips-icon.png

5. Enter the password to use for the Binding user in the **LDAP Bind Password** text field. In this example, the password is 'passme':

.. image:: ../common/images/configure-awx-auth-ldap-bind-pwd.png

6. Click to select a group type from the **LDAP Group Type** drop-down menu list. 

  LDAP Group Types include:

  - ``PosixGroupType``
  - ``GroupOfNamesType`` 
  - ``GroupOfUniqueNamesType`` 
  - ``ActiveDirectoryGroupType`` 
  - ``OrganizationalRoleGroupType`` 
  - ``MemberDNGroupType`` 
  - ``NISGroupType`` 
  - ``NestedGroupOfNamesType`` 
  - ``NestedGroupOfUniqueNamesType`` 
  - ``NestedActiveDirectoryGroupType`` 
  - ``NestedOrganizationalRoleGroupType`` 
  - ``NestedMemberDNGroupType`` 
  - ``PosixUIDGroupType``

  The LDAP Group Types that are supported by leveraging the underlying `django-auth-ldap library`_. To specify the parameters for the selected group type, see :ref:`Step 15 <ldap_grp_params>` below.

  .. _`django-auth-ldap library`: https://django-auth-ldap.readthedocs.io/en/latest/groups.html#types-of-groups


7. The **LDAP Start TLS** is disabled by default. To enable TLS when the LDAP connection is not using SSL, click the toggle to **ON**. 

.. image:: ../common/images/configure-awx-auth-ldap-start-tls.png

8. Enter the Distinguished Name in the **LDAP Bind DN** text field to specify the user that AWX uses to connect (Bind) to the LDAP server. Below uses the example, ``CN=josie,CN=users,DC=website,DC=com``:

.. image:: ../common/images/configure-awx-auth-ldap-bind-dn.png


9. If that name is stored in key ``sAMAccountName``, the **LDAP User DN Template** populates with ``(sAMAccountName=%(user)s)``. Active Directory stores the username to ``sAMAccountName``. Similarly, for OpenLDAP, the key is ``uid``--hence the line becomes ``(uid=%(user)s)``.

10. Enter the group distinguish name to allow users within that group to access AWX in the **LDAP Require Group** field, using the same format as the one shown in the text field, ``CN=awx Users,OU=Users,DC=website,DC=com``.

.. image:: ../common/images/configure-awx-auth-ldap-req-group.png

11. Enter the group distinguish name to prevent users within that group to access AWX in the **LDAP Deny Group** field, using the same format as the one shown in the text field. In this example, leave the field blank. 


12. Enter where to search for users while authenticating in the **LDAP User Search** field using the same format as the one shown in the text field. In this example, use:

::

  [
  "OU=Users,DC=website,DC=com",
  "SCOPE_SUBTREE",
  "(cn=%(user)s)"
  ]

The first line specifies where to search for users in the LDAP tree. In the above example, the users are searched recursively starting from ``DC=website,DC=com``.

The second line specifies the scope where the users should be searched:

  - SCOPE_BASE:  This value is used to indicate searching only the entry at the base DN, resulting in only that entry being returned
  - SCOPE_ONELEVEL:  This value is used to indicate searching all entries one level under the base DN - but not including the base DN and not including any entries under that one level under the base DN.
  - SCOPE_SUBTREE: This value is used to indicate searching of all entries at all levels under and including the specified base DN.

The third line specifies the key name where the user name is stored.

.. image:: ../common/images/configure-awx-authen-ldap-user-search.png

.. note::

  For multiple search queries, the proper syntax is:
  ::

    [
      [
      "OU=Users,DC=northamerica,DC=acme,DC=com",
      "SCOPE_SUBTREE",
      "(sAMAccountName=%(user)s)"
      ],
      [
      "OU=Users,DC=apac,DC=corp,DC=com",
      "SCOPE_SUBTREE",
      "(sAMAccountName=%(user)s)"
      ],
      [
      "OU=Users,DC=emea,DC=corp,DC=com",
      "SCOPE_SUBTREE",
      "(sAMAccountName=%(user)s)"
      ]
    ]


13. In the **LDAP Group Search** text field, specify which groups should be searched and how to search them. In this example, use:

::

  [
 "dc=example,dc=com",
 "SCOPE_SUBTREE",
 "(objectClass=group)"
  ]

- The first line specifies the BASE DN where the groups should be searched.
- The second lines specifies the scope and is the same as that for the user directive.
- The third line specifies what the ``objectclass`` of a group object is in the LDAP you are using.

.. image:: ../common/images/configure-awx-authen-ldap-group-search.png

14. Enter the user attributes in the **LDAP User Attribute Map** the text field. In this example, use:

::

  {
  "first_name": "givenName",
  "last_name": "sn",
  "email": "mail"
  }


The above example retrieves users by last name from the key ``sn``. You can use the same LDAP query for the user to figure out what keys they are stored under.

.. image:: ../common/images/configure-awx-auth-ldap-user-attrb-map.png

.. _ldap_grp_params:

15. Depending on the selected **LDAP Group Type**, different parameters are available in the **LDAP Group Type Parameters** field to account for this. ``LDAP_GROUP_TYPE_PARAMS`` is a dictionary, which will be converted by AWX to kwargs and passed to the LDAP Group Type class selected. There are two common parameters used by any of the LDAP Group Type; ``name_attr`` and ``member_attr``. Where ``name_attr`` defaults to ``cn`` and ``member_attr`` defaults to ``member``:

  ::

    {"name_attr": "cn", "member_attr": "member"}

  To determine what parameters a specific LDAP Group Type expects. refer to the `django_auth_ldap`_ documentation around the classes ``init`` parameters.

  .. _`django_auth_ldap`: https://django-auth-ldap.readthedocs.io/en/latest/reference.html#django_auth_ldap.config.LDAPGroupType


16. Enter the user profile flags in the **LDAP User Flags by Group** the text field. In this example, use the following syntax to set LDAP users as "Superusers" and "Auditors":

::

  {
  "is_superuser": "cn=superusers,ou=groups,dc=website,dc=com",
  "is_system_auditor": "cn=auditors,ou=groups,dc=website,dc=com"
  }

The above example retrieves users who are flagged as superusers or as auditor in their profile.

.. image:: ../common/images/configure-awx-auth-ldap-user-flags.png 

17. For details on completing the mapping fields, see :ref:`ag_ldap_org_team_maps`. 

.. image:: ../common/images/configure-ldap-orgs-teams-mapping.png

18. Click **Save** when done.

With these values entered on this form, you can now make a successful authentication with LDAP.

.. note::

  AWX does not actively sync users, but they are created during their initial login.
  To improve performance associated with LDAP authentication, see :ref:`ldap_auth_perf_tips` at the end of this chapter.


.. _ag_ldap_org_team_maps:

LDAP Organization and Team Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index:: 
   single: organization mapping
   single: LDAP mapping
   pair: authentication; LDAP mapping
   pair: authentication; organization mapping
   pair: authentication; LDAP team mapping
   pair: authentication; team mapping
   single: team mapping

You can control which users are placed into which organizations based on LDAP attributes (mapping out between your organization admins/users and LDAP groups).  

Keys are organization names. Organizations will be created if not present. Values are dictionaries defining the options for each organization's membership. For each organization, it is possible to specify what groups are automatically users of the organization and also what groups can administer the organization.  

**admins**: None, True/False, string or list/tuple of strings.
  - If **None**, organization admins will not be updated based on LDAP values.
  - If **True**, all users in LDAP will automatically be added as admins of the organization.
  - If **False**, no LDAP users will be automatically added as admins of the organization.
  - If a string or list of strings, specifies the group DN(s) that will be added of the organization if they match any of the specified groups.

**remove_admins**: True/False. Defaults to **False**. 
  - When **True**, a user who is not an member of the given groups will be removed from the organization's administrative list.

**users**: None, True/False, string or list/tuple of strings. Same rules apply as for **admins**.

**remove_users**: True/False. Defaults to **False**. Same rules apply as **remove_admins**.

::

  {
  "LDAP Organization": {
    "admins": "cn=engineering_admins,ou=groups,dc=example,dc=com",
    "remove_admins": false,
    "users": [
      "cn=engineering,ou=groups,dc=example,dc=com",
      "cn=sales,ou=groups,dc=example,dc=com",
      "cn=it,ou=groups,dc=example,dc=com"
    ],
    "remove_users": false
  },
  "LDAP Organization 2": {
    "admins": [
      "cn=Administrators,cn=Builtin,dc=example,dc=com"
    ],
    "remove_admins": false,
    "users": true,
    "remove_users": false
  }
  }

Mapping between team members (users) and LDAP groups. Keys are team names (will be created if not present). Values are dictionaries of options for each team's membership, where each can contain the following parameters:

**organization**: string. The name of the organization to which the team belongs. The team will be created if the combination of organization and team name does not exist. The organization will first be created if it does not exist.

**users**: None, True/False, string or list/tuple of strings.

  - If **None**, team members will not be updated.
  - If **True/False**, all LDAP users will be added/removed as team members.
  - If a string or list of strings, specifies the group DN(s). User will be added as a team member if the user is a member of ANY of these groups.

**remove**: True/False. Defaults to **False**. When **True**, a user who is not a member of the given groups will be removed from the team.

::

  {
  "LDAP Engineering": {
    "organization": "LDAP Organization",
    "users": "cn=engineering,ou=groups,dc=example,dc=com",
    "remove": true
  },
  "LDAP IT": {
    "organization": "LDAP Organization",
    "users": "cn=it,ou=groups,dc=example,dc=com",
    "remove": true
  },
  "LDAP Sales": {
    "organization": "LDAP Organization",
    "users": "cn=sales,ou=groups,dc=example,dc=com",
    "remove": true
  }
  }


.. _ldap_logging:

Enabling Logging for LDAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index:: 
   single: LDAP
   pair: authentication; LDAP

To enable logging for LDAP, you must set the level to ``DEBUG`` in the Settings configuration window: 

1. Click **Settings** from the left navigation pane and click to select **Logging settings** from the System list of options.
2. Click **Edit**.
3. Set the **Logging Aggregator Level Threshold** field to **Debug**.

.. image:: ../common/images/settings-system-logging-debug.png

4. Click **Save** to save your changes.


Referrals
~~~~~~~~~~~

.. index::
    pair: LDAP; referrals
    pair: troubleshooting; LDAP referrals

Active Directory uses "referrals" in case the queried object is not available in its database. It has been noted that this does not work properly with the django LDAP client and, most of the time, it helps to disable referrals. Disable LDAP referrals by adding the following lines to your ``/etc/awx/conf.d/custom.py`` file:

  .. code-block:: bash

    AUTH_LDAP_GLOBAL_OPTIONS = {
        ldap.OPT_REFERRALS: False,
    }


.. _ldap_auth_perf_tips:

LDAP authentication performance tips
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: best practices; ldap

When an LDAP user authenticates, by default, all user-related attributes will be updated in the database on each log in. In some environments, this operation can be skipped due to performance issues. To avoid it, you can disable the option `AUTH_LDAP_ALWAYS_UPDATE_USER`.

.. warning::

  
  With this option set to False, no changes to LDAP user's attributes will be updated. Attributes will only be updated the first time the user is created.

