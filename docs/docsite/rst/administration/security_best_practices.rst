
.. _ag_security_best_practices:

Security Best Practices
=========================

AWX is deployed in a secure fashion for use to automate typical environments. However, managing certain operating system environments, automation, and automation platforms, may require some additional best practices to ensure security. This document describes best practices for automation in a secure manner. 


Understand the architecture of Ansible and AWX
----------------------------------------------------------

Ansible and AWX comprise a general purpose, declarative, automation platform. That means that once an Ansible playbook is launched (via AWX, or directly on the command line), the playbook, inventory, and credentials provided to Ansible are considered to be the source of truth.  If policies are desired around external verification of specific playbook content, job definition, or inventory contents, these processes must be undertaken before the automation is launched (whether via the AWX web UI, or the AWX API).

These can take many forms. The use of source control, branching, and mandatory code review is best practice for Ansible automation. There are many tools that can help create process flow around using source control in this manner.

At a higher level, many tools exist that allow for creation of approvals and policy-based actions around arbitrary workflows, including automation; these tools can then use Ansible via AWX’s API to perform automation.

We recommend all customers of AWX select a secure default administrator password at time of installation.  See :ref:`tips_change_password` for more information.

AWX exposes services on certain well-known ports, such as port 80 for HTTP traffic and port 443 for HTTPS traffic.  We recommend that you do not expose AWX on the open internet, significantly reducing the threat surface of your installation.


Granting access
-----------------

Granting access to certain parts of the system exposes security risks. Apply the following practices to help secure access:

.. contents::
    :local:

Minimize administrative accounts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Minimizing the access to system administrative accounts is crucial for maintaining a secure system. A system administrator/root user can access, edit, and disrupt any system application. Keep the number of people/accounts with root access to as small of a group as possible. Do not give out `sudo` to `root` or `awx` (awx user) to untrusted users. Know that when restricting administrative access via mechanisms like `sudo`, that restricting to a certain set of commands may still give a wide range of access. Any command that allows for execution of a shell or arbitrary shell commands, or any command that can change files on the system, is fundamentally equivalent to full root access.

In an AWX context, any AWX ‘system administrator’ or ‘superuser’ account can edit, change, and update any inventory or automation definition in AWX. Restrict this to the minimum set of users possible for low-level AWX configuration and disaster recovery only.


Minimize local system access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

AWX, when used with best practices, should not require local user access except for administrative purposes. Non-administrator users should not have access to the AWX system.


Remove access to credentials from users
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If an automation credential is only stored in AWX, it can be further secured. Services such as OpenSSH can be configured to only allow credentials on connections from specific addresses. Credentials used by automation can be different than credentials used by system administrators for disaster-recovery or other ad-hoc management, allowing for easier auditing.

Enforce separation of duties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Different pieces of automation may need to access a system at different levels. For example, you may have low-level system automation that applies patches and performs security baseline checking, while a higher-level piece of automation deploys applications. By using different keys or credentials for each piece of automation, the effect of any one key vulnerability is minimized, while also allowing for easy baseline auditing.


Available resources
--------------------

Several resources exist in AWX and elsewhere to ensure a secure platform. Consider utilizing the following functionality:

.. contents::
    :local:


Audit and logging functionality
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For any administrative access, it is key to audit and watch for actions.

For AWX, this is done via the built-in Activity Stream support that logs all changes within AWX, as well as via the automation logs.

Best practices dictate collecting logging and auditing centrally, rather than reviewing it on the local system. It is recommended that AWX be configured to use whatever IDS and/or logging/auditing (Splunk) is standard in your environment. AWX includes built-in logging integrations for Elastic Stack, Splunk, Sumologic, Loggly, and more. See :ref:`ag_logging` for more information.


Existing security functionality
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Do not disable SELinux, and do not disable AWX’s existing multi-tenant containment. Use AWX’s role-based access control (RBAC) to delegate the minimum level of privileges required to run automation. Use Teams in AWX to assign permissions to groups of users rather than to users individually. See :ref:`rbac-ug` in the |atu|.


External account stores
^^^^^^^^^^^^^^^^^^^^^^^^^

Maintaining a full set of users just in AWX can be a time-consuming task in a large organization, prone to error. AWX supports connecting to external account sources via :ref:`LDAP <ag_auth_ldap>`, :ref:`SAML 2.0 <ag_auth_saml>`, and certain :ref:`OAuth providers <ag_social_auth>`. Using this eliminates a source of error when working with permissions.


.. _ag_security_django_password:

Django password policies
^^^^^^^^^^^^^^^^^^^^^^^^^^

AWX admins can leverage Django to set password policies at creation time via ``AUTH_PASSWORD_VALIDATORS`` to validate AWX user passwords. In the ``custom.py`` file located at ``/etc/awx/conf.d`` of your AWX instance, add the following code block example:

.. code-block:: text


	AUTH_PASSWORD_VALIDATORS = [
	    {
	        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	    },
	    {
	        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
	        'OPTIONS': {
	            'min_length': 9,
	        }
	    },
	    {
	        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
	    },
	    {
	        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
	    },
	]

For more information, see `Password management in Django <https://docs.djangoproject.com/en/3.2/topics/auth/passwords/#module-django.contrib.auth.password_validation>`_ in addition to the example posted above.

Be sure to restart your AWX instance for the change to take effect. See :ref:`ag_restart_awx` for detail.
