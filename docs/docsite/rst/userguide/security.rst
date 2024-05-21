 
.. _ug_security:

Security
=========

.. index::
   single: security

The following sections will help you gain an understanding of how AWX handles and lets you control file system security.

All playbooks are executed via the ``awx`` file system user. For running jobs, AWX offers job isolation via the use of Linux containers. This projection ensures jobs can only access playbooks, roles, and data from the Project directory for that job template.

For credential security, users may choose to upload locked SSH keys and set the unlock password to "ask". You can also choose to have the system prompt them for SSH credentials or sudo passwords rather than having the system store them in the database.


Playbook Access and Information Sharing
-----------------------------------------

.. index::
   pair: playbooks; sharing access
   pair: playbooks; sharing content
   pair: playbooks; process isolation


AWX's use of automation execution environments and Linux containers prevents playbooks from reading files outside of their project directory. 

By default, the only data exposed to the ansible-playbook process inside the container is the current project being used.

You can customize this in the Job Settings and expose additional directories from the host into the container. Refer the next section, :ref:`ug_isolation` for more information.

.. _ug_isolation:

Isolation functionality and variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
    pair: troubleshooting; isolation
    pair: isolation; functionality
    pair: isolation; variables

.. include:: ../common/isolation_variables.rst