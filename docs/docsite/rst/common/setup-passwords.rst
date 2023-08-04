
.. index::
   single: installation script; inventory file setup
   single: inventory file setup

As you edit your inventory file, there are a few things you must keep in mind:

- The contents of the inventory file should be defined in ``./inventory``, next to the ``./setup.sh`` installer playbook.

- For **installations and upgrades**: If you need to make use of external databases, you must ensure the database sections of your inventory file are properly setup. Edit this file and add your external database information before running the setup script.

- For **Ansible Automation Platform** or **Automation Hub**: Be sure to add an automation hub host in the [automationhub] group (Tower and Automation Hub cannot be installed on the same node).

- Tower will not configure replication or failover for the database that it uses, although Tower should work with any replication that you have.

- The database server should be on the same network or in the same data center as the Tower server for performance reasons.

- For **upgrading an existing cluster**: When upgrading a cluster, you may decide that you want to also reconfigure your cluster to omit existing instances or instance groups. Omitting the instance or the instance group from the inventory file will not be enough to remove them from the cluster. In addition to omitting instances or instance groups from the inventory file, you must also :ref:`deprovision instances or instance groups <administration:ag_cluster_deprovision>` before starting the upgrade. Otherwise, omitted instances or instance groups will continue to communicate with the cluster, which can cause issues with tower services during the upgrade.

- For **clustered installations**: If you are creating a clustered setup, you must replace ``localhost`` with the hostname or IP address of all instances. All nodes/instances must be able to reach any others using this hostname or address. In other words, you cannot use the ``localhost ansible_connection=local`` on one of the nodes *AND* all of the nodes should use the same format for the host names. 

  Therefore, this will *not* work:

  ::

    [tower]
    localhost ansible_connection=local
    hostA
    hostB.example.com
    172.27.0.4

  Instead, use these formats:

  ::

    [tower]
    hostA
    hostB
    hostC

  OR

  ::

      hostA.example.com
      hostB.example.com
      hostC.example.com

  OR

  ::
  
      [tower]
      172.27.0.2
      172.27.0.3
      172.27.0.4


- For **all standard installations**: When performing an installation, you must supply any necessary passwords in the inventory file.

.. note::
  
  Changes made to the installation process now require that you fill out all of the password fields in the inventory file. If you need to know where to find the values for these they should be:

    ``admin_password=''`` <--- Tower local admin password

    ``pg_password=''``  <---- Found in /etc/tower/conf.d/postgres.py

.. Warning::

  Do not use special characters in ``pg_password`` as it may cause the setup to fail.

Example Inventory files
^^^^^^^^^^^^^^^^^^^^^^^

- For **provisioning new nodes**: When provisioning new nodes add the nodes to the inventory file with all current nodes, make sure all passwords are included in the inventory file.

- For **upgrading a single node**: When upgrading, be sure to compare your inventory file to the current release version. It is recommended that you keep the passwords in here even when performing an upgrade.

------------------------------------------------
Example Standalone Automation Hub Inventory File
------------------------------------------------

::

  [automationhub]
  automationhub.acme.org
  [all:vars]
  automationhub_admin_password='<password>'
  automationhub_pg_host=''
  automationhub_pg_port=''
  automationhub_pg_database='automationhub'
  automationhub_pg_username='automationhub'
  automationhub_pg_password='<password>'
  automationhub_pg_sslmode='prefer'
  # The default install will deploy a TLS enabled Automation Hub.
  # If for some reason this is not the behavior wanted one can
  # disable TLS enabled deployment.
  #
  # automationhub_disable_https = False
  # The default install will generate self-signed certificates for the Automation
  # Hub service. If you are providing valid certificate via automationhub_ssl_cert
  # and automationhub_ssl_key, one should toggle that value to True.
  #
  # automationhub_ssl_validate_certs = False
  # SSL-related variables
  # If set, this will install a custom CA certificate to the system trust store.
  # custom_ca_cert=/path/to/ca.crt
  # Certificate and key to install in Automation Hub node
  # automationhub_ssl_cert=/path/to/automationhub.cert
  # automationhub_ssl_key=/path/to/automationhub.key

--------------------------------
Example Platform Inventory File
--------------------------------

::

  [tower]
  tower.acme.org
  [automationhub]
  automationhub.acme.org
  [database]
  database-01.acme.org
  [all:vars]
  admin_password='<password>'
  pg_host='database-01.acme.org'
  pg_port='5432'
  pg_database='awx'
  pg_username='awx'
  pg_password='<password>' 
  pg_sslmode='prefer'  # set to 'verify-full' for client-side enforced SSL
  # Automation Hub Configuration
  #
  automationhub_admin_password='<password>' 
  automationhub_pg_host='database-01.acme.org'
  automationhub_pg_port='5432'
  automationhub_pg_database='automationhub'
  automationhub_pg_username='automationhub'
  automationhub_pg_password='<password>'
  automationhub_pg_sslmode='prefer'
  # The default install will deploy a TLS enabled Automation Hub.
  # If for some reason this is not the behavior wanted one can
  # disable TLS enabled deployment.
  # 
  # automationhub_disable_https = False
  # The default install will generate self-signed certificates for the Automation
  # Hub service. If you are providing valid certificate via automationhub_ssl_cert
  # and automationhub_ssl_key, one should toggle that value to True.
  # 
  # automationhub_ssl_validate_certs = False
  # Isolated Tower nodes automatically generate an RSA key for authentication;
  # To disable this behavior, set this value to false
  # isolated_key_generation=true
  # SSL-related variables
  # If set, this will install a custom CA certificate to the system trust store.
  # custom_ca_cert=/path/to/ca.crt
  # Certificate and key to install in nginx for the web UI and API
  # web_server_ssl_cert=/path/to/tower.cert
  # web_server_ssl_key=/path/to/tower.key
  # Certificate and key to install in Automation Hub node
  # automationhub_ssl_cert=/path/to/automationhub.cert
  # automationhub_ssl_key=/path/to/automationhub.key
  # Server-side SSL settings for PostgreSQL (when we are installing it).
  # postgres_use_ssl=False
  # postgres_ssl_cert=/path/to/pgsql.crt
  # postgres_ssl_key=/path/to/pgsql.key

------------------------------------
Example Single Node Inventory File
------------------------------------

::

  [tower]
  localhost ansible_connection=local

  [database]

  [all:vars]
  admin_password='password'

  pg_host=''
  pg_port=''

  pg_database='awx'
  pg_username='awx'
  pg_password='password'


.. Warning::

  Do not use special characters in ``pg_password`` as it may cause the setup to fail.
  
-------------------------------------------
Example Multi Node Cluster Inventory File
-------------------------------------------

::

   [tower]
   clusternode1.example.com
   clusternode2.example.com
   clusternode3.example.com

   [database]
   dbnode.example.com

   [all:vars]
   ansible_become=true

   admin_password='password'

   pg_host='dbnode.example.com'
   pg_port='5432'

   pg_database='tower'
   pg_username='tower'
   pg_password='password'


.. Warning::

  Do not use special characters in ``pg_password`` as it may cause the setup to fail.

--------------------------------------------------------
Example Inventory file for an external existing database
--------------------------------------------------------

::

  [tower]
  node.example.com ansible_connection=local
  
  [database]
  
  [all:vars]
  admin_password='password'
  pg_password='password'

  
  pg_host='database.example.com'
  pg_port='5432'
  
  pg_database='awx'
  pg_username='awx'


.. Warning::

  Do not use special characters in ``pg_password`` as it may cause the setup to fail.


------------------------------------------------------------------------
Example Inventory file for external database which needs installation
------------------------------------------------------------------------

::


  [tower]
  node.example.com ansible_connection=local


  [database]
  database.example.com

  [all:vars]
  admin_password='password'
  pg_password='password'

  pg_host='database.example.com'
  pg_port='5432'

  pg_database='awx'
  pg_username='awx'


.. Warning::

  Do not use special characters in ``pg_password`` as it may cause the setup to fail.

Once any necessary changes have been made, you are ready to run ``./setup.sh``. 

.. note::

  Root access to the remote machines is required. With Ansible, this can be achieved in different ways:

    - ansible_user=root ansible_ssh_pass="your_password_here" inventory host or group variables
    - ansible_user=root ansible_ssh_private_key_file="path_to_your_keyfile.pem" inventory host or group variables
    - ANSIBLE_BECOME_METHOD='sudo' ANSIBLE_BECOME=True ./setup.sh
    - ANSIBLE_SUDO=True ./setup.sh (Only applies to Ansible 2.7)

  The ``DEFAULT_SUDO`` Ansible configuration parameter was removed in Ansible 2.8, which causes the ``ANSIBLE_SUDO=True ./setup.sh`` method of privilege escalation to no longer work. For more information on ``become`` plugins, refer to `Understanding Privilege Escalation`_ and the `list of become plugins`_.

    .. _`Understanding Privilege Escalation`: https://docs.ansible.com/ansible/latest/user_guide/become.html#understanding-privilege-escalation

    .. _`list of become plugins`: https://docs.ansible.com/ansible/latest/plugins/become.html#plugin-list
