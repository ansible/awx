.. _admin_troubleshooting:

***********************
Troubleshooting AWX
***********************

.. index:: 
   single: troubleshooting
   single: help
  
.. _admin_troubleshooting_extra_settings:

Error logging and extra settings
=================================
.. index::
   pair: troubleshooting; general help
   pair: troubleshooting; error logs

AWX server errors are streamed and not logged, however you may be able to pass them in on the AWX spec file.

With ``extra_settings``, you can pass multiple custom settings via the ``awx-operator``. The parameter ``extra_settings``  will be appended to the ``/etc/tower/settings.py`` file and can be an alternative to the ``extra_volumes`` parameter.

+----------------+----------------+---------+
| Name           | Description    | Default |
+----------------+----------------+---------+
| extra_settings | Extra settings | ''      |
+----------------+----------------+---------+

Parameters configured in ``extra_settings`` are set as read-only settings in AWX.  As a result, they cannot be changed in the UI after deployment. If you need to change the setting after the initial deployment, you need to change it on the AWX CR spec.  

Example configuration of ``extra_settings`` parameter:

::

   spec:
     extra_settings:
       - setting: MAX_PAGE_SIZE
         value: "500"
        
       - setting: AUTH_LDAP_BIND_DN
         value: "cn=admin,dc=example,dc=com"
      
       - setting: LOG_AGGREGATOR_LEVEL
         value: "'DEBUG'"

For some settings, such as ``LOG_AGGREGATOR_LEVEL``, the value may need double quotes as shown in the above example.

.. taken from https://github.com/ansible/awx-operator/blob/devel/docs/user-guide/advanced-configuration/extra-settings.md

.. _admin_troubleshooting_sosreport:

sosreport
==========
.. index::
   pair: troubleshooting; sosreport

The ``sosreport`` is a utility that collects diagnostic information for root cause analysis.


Problems connecting to your host
===================================

.. index::
   pair: troubleshooting; host connections

If you are unable to run the ``helloworld.yml`` example playbook from the Quick Start Guide or other playbooks due to host connection errors, try the following:

- Can you ``ssh`` to your host? Ansible depends on SSH access to the servers you are managing.
- Are your hostnames and IPs correctly added in your inventory file? (Check for typos.)

Unable to login to AWX via HTTP
==================================

Access to AWX is intentionally restricted through a secure protocol (HTTPS). In cases where your configuration is set up to run an AWX node behind a load balancer or proxy as "HTTP only", and you only want to access it without SSL (for troubleshooting, for example), you may change the settings of the ``/etc/tower/conf.d`` of your AWX instance. The operator has ``extra_settings`` that allows you to change a file-based setting in OCP. See :ref:`admin_troubleshooting_extra_settings` for detail.

Once in the spec, set the following accordingly:
 
:: 

  SESSION_COOKIE_SECURE = False
  CSRF_COOKIE_SECURE = False

Changing these settings to ``False`` will allow AWX to manage cookies and login sessions when using the HTTP protocol. This must be done on every node of a cluster installation to properly take effect.

To apply the changes, run:

::

   awx-service restart


WebSockets port for live events not working
===================================================

.. index::
   pair: live events; port changes
   pair: troubleshooting; live events
   pair: troubleshooting; websockets


AWX uses port 80/443 on the AWX server to stream live updates of playbook activity and other events to the client browser. These ports are configured for 80/443 by default, but if they are blocked by firewalls, close any firewall rules that opened up or added for the previous websocket ports, this will ensure your firewall allows traffic through this port.


Problems running a playbook
==============================

.. index::
   pair: troubleshooting; host connections

If you are unable to run the ``helloworld.yml`` example playbook from the Quick Start Guide or other playbooks due to playbook errors, try the following:

- Are you authenticating with the user currently running the commands? If not, check how the username has been setup or pass the ``--user=username`` or ``-u username`` commands to specify a user.
- Is your YAML file correctly indented? You may need to line up your whitespace correctly. Indentation level is significant in YAML. You can use ``yamlint`` to check your playbook. For more information, refer to the YAML primer at: http://docs.ansible.com/YAMLSyntax.html  
- Items beginning with a ``-`` are considered list items or plays. Items with the format of ``key: value`` operate as hashes or dictionaries. Ensure you don't have extra or missing ``-`` plays.


Problems when running a job
==============================

.. index::
   pair: troubleshooting; job does not run

If you are having trouble running a job from a playbook, you should review the playbook YAML file. When importing a playbook, either manually or via a source control mechanism, keep in mind that the host definition is controlled by AWX and should be set to ``hosts: all``. 


Playbooks aren't showing up in the "Job Template" drop-down
=============================================================

.. index::
    pair: playbooks are not viewable; Job Template drop-down list
    pair: troubleshooting; playbooks not appearing 

If your playbooks are not showing up in the Job Template drop-down list, here are a few things you can check:

- Make sure that the playbook is valid YML and can be parsed by Ansible.
- Make sure the permissions and ownership of the project path (/var/lib/awx/projects) is set up so that the "awx" system user can view the files. You can run this command to change the ownership:

::
  
    chown awx -R /var/lib/awx/projects/


Playbook stays in pending
===========================
.. index::
   pair: troubleshooting; pending playbook

If you are attempting to run a playbook Job and it stays in the "Pending" state indefinitely, try the following:

- Ensure all supervisor services are running via ``supervisorctl status``.
- Check to ensure that the ``/var/`` partition has more than 1 GB of space available. Jobs will not complete with insufficient space on the ``/var/`` partition.
- Run ``awx-service restart`` on the AWX server.


If you continue to have problems, run ``sosreport`` as root on the AWX server, then file a `support request`_ with the result.

.. _`support request`: http://support.ansible.com/


Cancel an AWX job
=========================
.. index:: 
   pair: troubleshooting; job cancellation

When issuing a ``cancel`` request on a currently running AWX job, AWX issues a ``SIGINT`` to the ``ansible-playbook`` process. While this causes Ansible to stop dispatching new tasks and exit, in many cases, module tasks that were already dispatched to remote hosts will run to completion. This behavior is similar to pressing ``Ctrl-C`` during a command-line Ansible run.
 
With respect to software dependencies, if a running job is canceled, the job is essentially removed but the dependencies will remain.



Reusing an external database causes installations to fail
=============================================================
.. index::
   pair: installation failure; external database

Instances have been reported where reusing the external DB during subsequent installation of nodes causes installation failures.

For example, say that you performed a clustered installation. Next, say that you needed to do this again and performed a second clustered installation reusing the same external database, only this subsequent installation failed.   

When setting up an external database which has been used in a prior installation, the database used for the clustered node must be manually cleared before any additional installations can succeed.


Private EC2 VPC Instances in the AWX Inventory
=======================================================

.. index::
    pair: EC2; VPC instances
    pair: troubleshooting; EC2 VPC instances


By default, AWX only shows instances in a VPC that have an Elastic IP (EIP) associated with them. To see all of your VPC instances, perform the following steps:

1. In the AWX interface, select your inventory. 
2. Click on the group that has the Source set to AWS, and click on the Source tab. 
3. In the ``Source Variables`` box, enter:

::

   vpc_destination_variable: private_ip_address 

Next, save and then trigger an update of the group. Once this is done, you should be able to see all of your VPC instances.

.. note::

  AWX must be running inside the VPC with access to those instances if you want to configure them.



Troubleshooting "Error: provided hosts list is empty"
======================================================

.. index::
    pair: troubleshooting; hosts list
    single: hosts lists (empty)

If you receive the message "Skipping: No Hosts Matched" when you are trying to run a playbook through AWX, here are a few things to check:

- Make sure that your hosts declaration line in your playbook matches the name of your group/host in inventory exactly (these are case sensitive).  
- If it does match and you are using Ansible Core 2.0 or later, check your group names for spaces and modify them to use underscores or no spaces to ensure that the groups can be recognized.
- Make sure that if you have specified a Limit in the Job Template that it is a valid limit value and still matches something in your inventory. The Limit field takes a pattern argument, described here: http://docs.ansible.com/intro_patterns.html

Please file a support ticket if you still run into issues after checking these options.
