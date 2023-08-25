
.. index::
   pair: installation script; playbook setup
   single: playbook setup
   pair: playbook setup; setup.sh

AWX setup playbook script uses the ``inventory`` file and is invoked as ``./setup.sh`` from the path where you unpacked the AWX installer tarball.  

::

    root@localhost:~$ ./setup.sh


The setup script takes the following arguments:

- ``-h`` -- Show this help message and exit
- ``-i INVENTORY_FILE`` -- Path to Ansible inventory file (default: ``inventory``)
- ``-e EXTRA_VARS`` -- Set additional Ansible variables as key=value or YAML/JSON (i.e. ``-e bundle_install=false`` forces an online installation)
- ``-b`` -- Perform a database backup in lieu of installing
- ``-r`` -- Perform a database restore in lieu of installing (a default restore path is used unless EXTRA_VARS are provided with a non-default path, as shown in the code example below)
	
::

		./setup.sh -e 'restore_backup_file=/path/to/nondefault/location' -r	
