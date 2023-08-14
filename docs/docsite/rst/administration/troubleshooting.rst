.. _admin_troubleshooting:

**************************************
Troubleshooting the controller
**************************************

.. index:: 
   single: troubleshooting
   single: help
  

Error logs
================
.. index::
   pair: troubleshooting; general help
   pair: troubleshooting; error logs

The controller server errors are logged in ``/var/log/tower``. Supervisors logs can be found in ``/var/log/supervisor/``. Nginx web server errors are logged in the httpd error log. Configure other controller logging needs in ``/etc/tower/conf.d/``.


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

Unable to login to the controller via HTTP
=============================================

Access to the controller is intentionally restricted through a secure protocol (HTTPS). In cases where your configuration is set up to run a controller node behind a load balancer or proxy as "HTTP only", and you only want to access it without SSL (for troubleshooting, for example), you must add the following settings in the ``custom.py`` file located at ``/etc/tower/conf.d`` of your controller instance:
 
:: 

  SESSION_COOKIE_SECURE = False
  CSRF_COOKIE_SECURE = False

Changing these settings to ``False`` will allow the controller to manage cookies and login sessions when using the HTTP protocol. This must be done on every node of a cluster installation to properly take effect.

To apply the changes, run:

::

   automation-controller-service restart


WebSockets port for live events not working
===================================================

.. index::
   pair: live events; port changes
   pair: troubleshooting; live events
   pair: troubleshooting; websockets


|at| uses port 80/443 on the controller server to stream live updates of playbook activity and other events to the client browser. These ports are configured for 80/443 by default, but if they are blocked by firewalls, close any firewall rules that opened up or added for the previous websocket ports, this will ensure your firewall allows traffic through this port.


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

If you are having trouble running a job from a playbook, you should review the playbook YAML file. When importing a playbook, either manually or via a source control mechanism, keep in mind that the host definition is controlled by the controller and should be set to ``hosts: all``. 


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
- Run ``automation-controller-service restart`` on the controller server.


If you continue to have problems, run ``sosreport`` as root on the controller server, then file a `support request`_ with the result.

.. _`support request`: http://support.ansible.com/


Cancel a controller job
=========================
.. index:: 
   pair: troubleshooting; job cancellation

When issuing a ``cancel`` request on a currently running controller job, the controller issues a ``SIGINT`` to the ``ansible-playbook`` process. While this causes Ansible to stop dispatching new tasks and exit, in many cases, module tasks that were already dispatched to remote hosts will run to completion. This behavior is similar to pressing ``Ctrl-C`` during a command-line Ansible run.
 
With respect to software dependencies, if a running job is canceled, the job is essentially removed but the dependencies will remain.



Reusing an external database causes installations to fail
=============================================================
.. index::
   pair: installation failure; external database

Instances have been reported where reusing the external DB during subsequent installation of nodes causes installation failures.

For example, say that you performed a clustered installation. Next, say that you needed to do this again and performed a second clustered installation reusing the same external database, only this subsequent installation failed.   

When setting up an external database which has been used in a prior installation, the database used for the clustered node must be manually cleared before any additional installations can succeed.


Private EC2 VPC Instances in the controller Inventory
=======================================================

.. index::
    pair: EC2; VPC instances
    pair: troubleshooting; EC2 VPC instances


By default, the controller only shows instances in a VPC that have an Elastic IP (EIP) associated with them. To see all of your VPC instances, perform the following steps:

1. In the controller interface, select your inventory. 
2. Click on the group that has the Source set to AWS, and click on the Source tab. 
3. In the ``Source Variables`` box, enter:

::

   vpc_destination_variable: private_ip_address 

Next, save and then trigger an update of the group. Once this is done, you should be able to see all of your VPC instances.

.. note::

  The controller must be running inside the VPC with access to those instances if you want to configure them.



Troubleshooting "Error: provided hosts list is empty"
======================================================

.. index::
    pair: troubleshooting; hosts list
    single: hosts lists (empty)

If you receive the message "Skipping: No Hosts Matched" when you are trying to run a playbook through the controller, here are a few things to check:

- Make sure that your hosts declaration line in your playbook matches the name of your group/host in inventory exactly (these are case sensitive).  
- If it does match and you are using Ansible Core 2.0 or later, check your group names for spaces and modify them to use underscores or no spaces to ensure that the groups can be recognized.
- Make sure that if you have specified a Limit in the Job Template that it is a valid limit value and still matches something in your inventory. The Limit field takes a pattern argument, described here: http://docs.ansible.com/intro_patterns.html

Please file a support ticket if you still run into issues after checking these options.
