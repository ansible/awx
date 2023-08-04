.. _ag_restart_tower:

Starting, Stopping, and Restarting the Controller
-------------------------------------------------------------------

.. index::
   single: controller admin utility script
   single: admin utility script
   single: scripts, admin utility
   single: init script replacement
   single: ansible-controller script replacement
   single: start controller
   single: stop controller
   single: restart controller


|At| ships with an *admin utility script*, ``automation-controller-service``, that can start, stop, and restart all the controller services running on the current single controller node (including the message queue components, and the database if it is an integrated installation). External databases must be explicitly managed by the administrator. The services script resides in ``/usr/bin/automation-controller-service`` and can be invoked as follows:

::

    root@localhost:~$ automation-controller-service restart


.. note::

    In clustered installs, ``automation-controller-service restart`` does not include PostgreSQL as part of the services that are restarted because it exists external to the controller, and because PostgreSQL does not always require a restart. Use ``systemctl restart automation-controller`` to restart services on clustered environments instead. Also you must restart each cluster node for certain changes to persist as opposed to a single node for a localhost install. For more information on clustered environments, see the :ref:`ag_clustering` section.


You can also invoke the services script via distribution-specific service management commands. Distribution packages often provide a similar script, sometimes as an init script, to manage services. Refer to your distribution-specific service management system for more information.

.. note::

    When running the controller in a container, do not use the ``automation-controller-service`` script. Restart the pod using the container environment instead.




