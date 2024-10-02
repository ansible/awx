.. _ag_social_auth:

Setting up Social Authentication
==================================

.. index::
    single: social authentication
    single: authentication

Authentication methods help simplify logins for end users--offering single sign-ons using existing login information to sign into a third party website rather than creating a new login account specifically for that website. 

Account authentication can be configured in the AWX User Interface and saved to the PostgreSQL database. For instructions, refer to the :ref:`ag_configure_awx` section. 

.. _ag_org_team_maps:

Organization and Team Mapping
---------------------------------

.. index:: 
   single: organization mapping
   pair: authentication; organization mapping
   pair: authentication; team mapping
   single: team mapping

Organization mapping
~~~~~~~~~~~~~~~~~~~~~

You will need to control which users are placed into which organizations based on their username and email address (mapping out your organization admins/users from social or enterprise-level authentication accounts).  

Dictionary keys are organization names. Organizations will be created, if not already present and if the license allows for multiple organizations. Otherwise, the single default organization is used regardless of the key.  

Values are dictionaries defining the options for each organization's membership.  For each organization, it is possible to specify which users are automatically users of the organization and also which users can administer the organization. 

**admins**: None, True/False, string or list/tuple of strings.

 - If **None**, organization admins will not be updated.
 - If **True**, all users using account authentication will automatically be added as admins of the organization.
 - If **False**, no account authentication users will be automatically added as admins of the organization.
 - If a string or list of strings, specifies the usernames and emails for users who will be added to the organization. Strings beginning and ending with ``/`` will be compiled into regular expressions; modifiers ``i`` (case-insensitive) and ``m`` (multi-line) may be specified after the ending ``/``.

**remove_admins**: True/False. Defaults to **True**.

 - When **True**, a user who does not match is removed from the organization's administrative list.

**users**: None, True/False, string or list/tuple of strings. Same rules apply as for **admins**.

**remove_users**: True/False. Defaults to **True**. Same rules apply as for **remove_admins**.


::

    {
        "Default": {
            "users": true
        },
        "Test Org": {
            "admins": ["admin@example.com"],
            "users": true
        },
        "Test Org 2": {
            "admins": ["admin@example.com", "/^awx-[^@]+?@.*$/i"],
            "users": "/^[^@].*?@example\\.com$/"
        }
    }

Organization mappings may be specified separately for each account authentication backend.  If defined, these configurations will take precedence over the global configuration above.

::

Team mapping
~~~~~~~~~~~~~~

Team mapping is the mapping of team members (users) from social auth accounts. Keys are team names (will be created if not present). Values are dictionaries of options for each team's membership, where each can contain the following parameters:

**organization**: string. The name of the organization to which the team
belongs.  The team will be created if the combination of organization and
team name does not exist.  The organization will first be created if it
does not exist.  If the license does not allow for multiple organizations,
the team will always be assigned to the single default organization.

**users**: None, True/False, string or list/tuple of strings.

 - If **None**, team members will not be updated.
 - If **True**/**False**, all social auth users will be added/removed as team members.
 - If a string or list of strings, specifies expressions used to match users. User will be added as a team member if the username or email matches. Strings beginning and ending with ``/`` will be compiled into regular expressions; modifiers ``i`` (case-insensitive) and ``m`` (multi-line) may be specified after the ending ``/``.

**remove**: True/False. Defaults to **True**. When **True**, a user who does not match the rules above is removed from the team.

::

    {
        "My Team": {
            "organization": "Test Org",
            "users": ["/^[^@]+?@test\\.example\\.com$/"],
            "remove": true
        },
        "Other Team": {
            "organization": "Test Org 2",
            "users": ["/^[^@]+?@test\\.example\\.com$/"],
            "remove": false
        }
    }


Team mappings may be specified separately for each account authentication backend, based on which of these you setup.  When defined, these configurations take precedence over the global configuration above.

::

    SOCIAL_AUTH_GITHUB_TEAM_MAP = {}
    SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP = {}
    SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP = {}

Uncomment the line below (i.e. set ``SOCIAL_AUTH_USER_FIELDS`` to an empty list) to prevent new user accounts from being created.  Only users who have previously logged in to AWX using social or enterprise-level authentication or have a user account with a matching email address will be able to login.

::

    SOCIAL_AUTH_USER_FIELDS = []

