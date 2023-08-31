.. _ag_manage_utility:

The *awx-manage* Utility
-------------------------------

.. index:: 
   single: awx-manage

The ``awx-manage`` utility is used to access detailed internal information of AWX. Commands for ``awx-manage`` should run as the ``awx`` or ``root`` user.

.. warning:: 
         Running awx-manage commands via playbook is not recommended or supported.

Inventory Import
~~~~~~~~~~~~~~~~

.. index:: 
   single: awx-manage; inventory import

``awx-manage`` is a mechanism by which an AWX administrator can import inventory directly into AWX, for those who cannot use Custom Inventory Scripts.

To use ``awx-manage`` properly, you must first create an inventory in AWX to use as the destination for the import.

For help with ``awx-manage``, run the following command: ``awx-manage inventory_import [--help]``

The ``inventory_import`` command synchronizes an AWX inventory object with a text-based inventory file, dynamic inventory script, or a directory of one or more of the above as supported by core Ansible.

When running this command, specify either an ``--inventory-id`` or ``--inventory-name``, and the path to the Ansible inventory source (``--source``).

::

    awx-manage inventory_import --source=/ansible/inventory/ --inventory-id=1 

By default, inventory data already stored in AWX blends with data from the external source. To use only the external data, specify ``--overwrite``. To specify that any existing hosts get variable data exclusively from the ``--source``, specify ``--overwrite_vars``. The default behavior adds any new variables from the external source, overwriting keys that already exist, but preserves any variables that were not sourced from the external data source.

::

    awx-manage inventory_import --source=/ansible/inventory/ --inventory-id=1 --overwrite


.. include:: ../common/overwrite_var_note_2-4-0.rst


Cleanup of old data
~~~~~~~~~~~~~~~~~~~

.. index:: 
   single: awx-manage, data cleanup

``awx-manage`` has a variety of commands used to clean old data from AWX. The AWX administrators can use the Management Jobs interface for access or use the command line. 

-  ``awx-manage cleanup_jobs [--help]``

This permanently deletes the job details and job output for jobs older than a specified number of days.

-  ``awx-manage cleanup_activitystream [--help]``

This permanently deletes any :ref:`ug_activitystreams` data older than a specific number of days.

Cluster management
~~~~~~~~~~~~~~~~~~~~

.. index:: 
   single: awx-manage; cluster management

Refer to the :ref:`ag_clustering` section for details on the
``awx-manage provision_instance`` and ``awx-manage deprovision_instance``
commands.


.. note::
    Do not run other ``awx-manage`` commands unless instructed by Ansible Support.


.. _ag_token_utility:

Token and session management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index:: 
   single: awx-manage; token management
   single: awx-manage; session management

AWX supports the following commands for OAuth2 token management:

.. contents::
    :local:


``create_oauth2_token``
^^^^^^^^^^^^^^^^^^^^^^^^

Use this command to create OAuth2 tokens (specify actual username for ``example_user`` below):

::

	$ awx-manage create_oauth2_token --user example_user

	New OAuth2 token for example_user: j89ia8OO79te6IAZ97L7E8bMgXCON2

Make sure you provide a valid user when creating tokens. Otherwise, you will get an error message that you tried to issue the command without specifying a user, or supplying a username that does not exist.


.. _ag_manage_utility_revoke_tokens:
 

``revoke_oauth2_tokens``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use this command to revoke OAuth2 tokens (both application tokens and personal access tokens (PAT)). By default, it revokes all application tokens (but not their associated refresh tokens), and revokes all personal access tokens. However, you can also specify a user for whom to revoke all tokens.

To revoke all existing OAuth2 tokens: 

::

	$ awx-manage revoke_oauth2_tokens

To revoke all OAuth2 tokens & their refresh tokens: 

::

	$ awx-manage revoke_oauth2_tokens --revoke_refresh

To revoke all OAuth2 tokens for the user with ``id=example_user`` (specify actual username for ``example_user`` below):

::

	$ awx-manage revoke_oauth2_tokens --user example_user

To revoke all OAuth2 tokens and refresh token for the user with ``id=example_user``:

::

	$ awx-manage revoke_oauth2_tokens --user example_user --revoke_refresh



``cleartokens``
^^^^^^^^^^^^^^^^^^^

Use this command to clear tokens which have already been revoked. Refer to `Django's Oauth Toolkit documentation on cleartokens`_ for more detail.

	.. _`Django's Oauth Toolkit documentation on cleartokens`: https://django-oauth-toolkit.readthedocs.io/en/latest/management_commands.html


``expire_sessions``
^^^^^^^^^^^^^^^^^^^^^^^^

Use this command to terminate all sessions or all sessions for a specific user. Consider using this command when a user changes role in an organization, is removed from assorted groups in LDAP/AD, or the administrator wants to ensure the user can no longer execute jobs due to membership in these groups.

::

	$ awx-manage expire_sessions


This command terminates all sessions by default. The users associated with those sessions will be consequently logged out. To only expire the sessions of a specific user, you can pass their username using the ``--user`` flag (specify actual username for ``example_user`` below):

::

	$ awx-manage expire_sessions --user example_user



``clearsessions``
^^^^^^^^^^^^^^^^^^^^^^^^

Use this command to delete all sessions that have expired. Refer to `Django's documentation on clearsessions`_ for more detail.

	.. _`Django's documentation on clearsessions`: https://docs.djangoproject.com/en/2.1/topics/http/sessions/#clearing-the-session-store



For more information on OAuth2 token management in the AWX user interface, see the :ref:`ug_applications_auth` section of the |atu|.


Analytics gathering
~~~~~~~~~~~~~~~~~~~~~

.. index:: 
   single: awx-manage; data collection
   single: awx-manage; analytics gathering


Use this command to gather analytics on-demand outside of the predefined window (default is 4 hours):

::

	$ awx-manage gather_analytics --ship


For customers with disconnected environments who want to collect usage information about unique hosts automated across a time period, use this command: 

::

  awx-manage host_metric --since YYYY-MM-DD --until YYYY-MM-DD --json


The parameters ``--since`` and ``--until`` specify date ranges and are optional, but one of them has to be present. The ``--json`` flag specifies the output format and is optional.
