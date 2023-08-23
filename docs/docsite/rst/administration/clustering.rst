
.. _ag_clustering:

Clustering
============

.. index::
   pair: redundancy; instance groups
   pair: redundancy; clustering

Clustering is sharing load between hosts. Each instance should be able to act as an entry point for UI and API access. This should enable the controller administrators to use load balancers in front of as many instances as they wish and maintain good data visibility.

.. note::
	Load balancing is optional and is entirely possible to have ingress on one or all instances as needed.

Each instance should be able to join the controller cluster and expand its ability to execute jobs. This is a simple system where jobs can and will run anywhere rather than be directed on where to run. Also, clustered instances can be grouped into different pools/queues, called :ref:`ag_instance_groups`.

AWX supports container-based clusters using Kubernetes, meaning new controller instances can be installed on this platform without any variation or diversion in functionality. You can create instance groups to point to a Kubernetes container. For more detail, see the :ref:`ag_ext_exe_env` section.


**Supported Operating Systems**

.. index::
   single: clustering; operating systems
   pair: clustering; RHEL
   pair: clustering; Centos

The following operating systems are supported for establishing a clustered environment:

- |rhel| 8 or later (RHEL9 recommended)


.. note::
        Isolated instances are not supported in conjunction with running |at| in OpenShift.


Setup Considerations
---------------------

.. index::
   single: clustering; setup considerations
   pair: clustering; PostgreSQL

This section covers initial setup of clusters only. For upgrading an existing cluster, refer to the |atumg|.

Important considerations to note in the new clustering environment:

- PostgreSQL is still a standalone instance and is not clustered. The controller does not manage replica configuration or database failover (if the user configures standby replicas). 

- When spinning up a cluster, the database node should be a standalone server, and PostgreSQL should not be installed on one of the controller nodes.

- PgBouncer is not recommended for connection pooling with AWX. Currently, AWX relies heavily on ``pg_notify`` for sending messages across various components, and therefore, PgBouncer cannot readily be used in transaction pooling mode.

- The maximum supported instances in a cluster is 20.

- All instances should be reachable from all other instances and they should be able to reach the database. It is also important for the hosts to have a stable address and/or hostname (depending on how the controller host is configured).

- All instances must be geographically collocated, with reliable low-latency connections between instances.

- For purposes of upgrading to a clustered environment, your primary instance must be part of the ``default`` group in the inventory *AND* it needs to be the first host listed in the ``default`` group.

- Manual projects must be manually synced to all instances by the customer, and updated on all instances at once.

- The ``inventory`` file for platform deployments should be saved/persisted. If new instances are to be provisioned, the passwords and configuration options, as well as host names, must be made available to the installer.


Install and Configure
-----------------------

Provisioning new instances involves updating the ``inventory`` file and re-running the setup playbook. It is important that the ``inventory`` file contains all passwords and information used when installing the cluster or other instances may be reconfigured. The ``inventory`` file inventory contains a single inventory group, ``automationcontroller``. 

.. note::
    All instances are responsible for various housekeeping tasks related to task scheduling, like determining where jobs are supposed to be launched and processing playbook events, as well as periodic cleanup.

::

		[automationcontroller]
		hostA
		hostB
		hostC

		[instance_group_east]
		hostB
		hostC

		[instance_group_west]
		hostC
		hostD

.. note::
	If no groups are selected for a resource then the ``automationcontroller`` group is used, but if any other group is selected, then the ``automationcontroller`` group will not be used in any way. 

The ``database`` group remains for specifying an external PostgreSQL. If the database host is provisioned separately, this group should be empty:

::

		[automationcontroller]
		hostA
		hostB
		hostC

		[database]
		hostDB

When a playbook runs on an individual controller instance in a cluster, the output of that playbook is broadcast to all of the other nodes as part of the controller's websocket-based streaming output functionality.  It is best to handle this data broadcast using internal addressing by specifying a private routable address for each node in your inventory:

  ::		

  		[automationcontroller]		
 		hostA routable_hostname=10.1.0.2		
 		hostB routable_hostname=10.1.0.3		
 		hostC routable_hostname=10.1.0.4

.. note::
	
	Prior versions of |at| used the variable name ``rabbitmq_host``. If you are upgrading from a previous version of the platform, and you previously specified ``rabbitmq_host`` in your inventory, simply rename ``rabbitmq_host`` to ``routable_hostname`` before upgrading.


Instances and Ports Used by the Controller and Automation Hub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ports and instances used by the controller and also required by the on-premise |ah| node are as follows:

- 80, 443 (normal controller and |ah| ports)

- 22 (ssh - ingress only required)

- 5432 (database instance - if the database is installed on an external instance, needs to be opened to the controller instances)


Status and Monitoring via Browser API
--------------------------------------

The controller itself reports as much status as it can via the Browsable API at ``/api/v2/ping`` in order to provide validation of the health of the cluster, including:

- The instance servicing the HTTP request

- The timestamps of the last heartbeat of all other instances in the cluster

- Instance Groups and Instance membership in those groups

View more details about Instances and Instance Groups, including running jobs and membership information at ``/api/v2/instances/`` and ``/api/v2/instance_groups/``.


Instance Services and Failure Behavior
----------------------------------------

Each controller instance is made up of several different services working collaboratively:

- HTTP Services - This includes the controller application itself as well as external web services.

- Callback Receiver - Receives job events from running Ansible jobs.

- Dispatcher - The worker queue that processes and runs all jobs.

- Redis - This key value store is used as a queue for event data propagated from ansible-playbook to the application.

- Rsyslog - log processing service used to deliver logs to various external logging services.

The controller is configured in such a way that if any of these services or their components fail, then all services are restarted. If these fail sufficiently often in a short span of time, then the entire instance will be placed offline in an automated fashion in order to allow remediation without causing unexpected behavior.


Job Runtime Behavior
---------------------

The way jobs are run and reported to a 'normal' user of controller does not change. On the system side, some differences are worth noting:

- When a job is submitted from the API interface it gets pushed into the dispatcher queue.  Each controller instance will connect to and receive jobs from that queue using a particular scheduling algorithm. Any instance in the cluster is just as likely to receive the work and execute the task. If a instance fails while executing jobs, then the work is marked as permanently failed.

|Controller Cluster example|

.. |Controller Cluster example| image:: ../common/images/clustering-visual.png

- Project updates run successfully on any instance that could potentially run a job. Projects will sync themselves to the correct version on the instance immediately prior to running the job. If the needed revision is already locally checked out and Galaxy or Collections updates are not needed, then a sync may not be performed. 

- When the sync happens, it is recorded in the database as a project update with a ``launch_type = sync`` and ``job_type =  run``. Project syncs will not change the status or version of the project; instead, they will update the source tree *only* on the instance where they run. 

- If updates are needed from Galaxy or Collections, a sync is performed that downloads the required roles, consuming that much more space in your /tmp file. In cases where you have a big project (around 10 GB), disk space on ``/tmp`` may be an issue.


Job Runs
^^^^^^^^^^^

By default, when a job is submitted to the controller queue, it can be picked up by any of the workers. However, you can control where a particular job runs, such as restricting the instances from which a job runs on. 

In order to support temporarily taking an instance offline, there is a property enabled defined on each instance. When this property is disabled, no jobs will be assigned to that instance. Existing jobs will finish, but no new work will be assigned.


.. _ag_cluster_deprovision:

Deprovision Instances
------------------------

.. index::
   pair: cluster; deprovisioning

Re-running the setup playbook does not automatically deprovision instances since clusters do not currently distinguish between an instance that was taken offline intentionally or due to failure. Instead, shut down all services on the controller instance and then run the deprovisioning tool from any other instance:

#. Shut down the instance or stop the service with the command, ``automation-controller-service stop``.

#. Run the deprovision command ``$ awx-manage deprovision_instance --hostname=<name used in inventory file>`` from another instance to remove it from the controller cluster.

	Example: ``awx-manage deprovision_instance --hostname=hostB``


Similarly, deprovisioning instance groups in the controller does not automatically deprovision or remove instance groups. For more information, refer to the :ref:`ag_instancegrp_deprovision` section. 
