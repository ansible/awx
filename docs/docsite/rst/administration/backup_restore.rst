.. _ag_backup_restore:

*************************
Backing Up and Restoring 
*************************

.. index::
   single: backups
   single: restorations

.. https://support.ansible.com/hc/en-us/articles/203295497-Tower-Manual-Backup-Restore

The ability to backup and restore your system(s) is integrated into the platform setup playbook. Refer to :ref:`ag_clustering_backup_restore` for additional considerations.

.. note:: 

  When restoring, be sure to restore to the same version from which it was backed up. However, you should always use the most recent minor version of a release to backup and/or restore your platform installation version. For example, if the current platform version you are on is 2.0.x, use only the latest 2.0 installer. 

  Also, backup and restore will *only* work on PostgreSQL versions supported by your current platform version. For more information, see `System Requirements <https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/2.0-ea/html-single/red_hat_ansible_automation_platform_installation_guide/index?lb_target=production#red_hat_ansible_automation_platform_system_requirements>`_. 


The platform setup playbook is invoked as ``setup.sh`` from the path where you unpacked the platform installer tarball. It uses the same inventory file used by the install playbook. The setup script takes the following arguments for backing up and restoring:

.. index::
   single: playbook setup; backup/restore arguments
   single: installation wizard; playbook backup/restore arguments

-  ``-b`` Perform a database backup rather than an installation.
-  ``-r`` Perform a database restore rather than an installation.

As the root user, call ``setup.sh`` with the appropriate parameters and the platform backup or restored as configured.

::

    root@localhost:~# ./setup.sh -b


::

    root@localhost:~# ./setup.sh -r


Backup files will be created on the same path that setup.sh script exists. It can be changed by specifying the following ``EXTRA_VARS`` :

::

    root@localhost:~# ./setup.sh -e 'backup_dest=/path/to/backup_dir/' -b


A default restore path is used unless ``EXTRA_VARS`` are provided with a non-default path, as shown in the example below:

::

    root@localhost:~# ./setup.sh -e 'restore_backup_file=/path/to/nondefault/backup.tar.gz' -r


Optionally, you can override the inventory file used by passing it as an argument to the setup script: 

::
  
    setup.sh -i <inventory file>


Backup/Restore Playbooks
================================

.. index::
   single: backups; playbooks
   single: restorations; playbooks


In addition to the ``install.yml`` file included with your ``setup.sh`` setup playbook, there are also ``backup.yml`` and ``restore.yml`` files for your backup and restoration needs.

These playbooks serve two functions--backup and restore.

- The overall backup will backup:

  1. the database
  2. the ``SECRET_KEY`` file

- The per-system backups include:
  
  1. custom user config files
  2. manual projects

- The restore will restore the backed up files and data to a freshly installed and working second instance of the controller.

When restoring your system, the installer checks to see that the backup file exists before beginning the restoration. If the backup file is not available, your restoration will fail.

.. note::

    Ensure your controller host(s) are properly set up with SSH keys or user/pass variables in the hosts file, and that the user has sudo access. 


Backup and Restoration Considerations 
==========================================

.. index::
   single: backups; considerations
   single: restorations; considerations

- Disk Space: Review your disk space requirements to ensure you have enough room to backup configuration files, keys, and other relevant files, plus the database of the platform installation.
- System Credentials: Confirm you have the system credentials you need when working with a local database or a remote database. On local systems, you may need root or ``sudo`` access, depending on how credentials were setup. On remote systems, you may need different credentials to grant you access to the remote system you are trying to backup or restore.
- You should always use the most recent minor version of a release to backup and/or restore your platform installation version. For example, if the current platform version you are on is 2.0.x, use only the latest 2.0 installer. 
- When using ``setup.sh`` to do a restore from the default restore file path, ``/var/lib/awx``, ``-r`` is still required in order to do the restore, but it no longer accepts an argument. If a non-default restore file path is needed, the user must provide this as an extra var (``root@localhost:~# ./setup.sh -e 'restore_backup_file=/path/to/nondefault/backup.tar.gz' -r``).
- If the backup file is placed in the same directory as the ``setup.sh`` installer, the restore playbook will automatically locate the restore files. In this case, you do not need to use the ``restore_backup_file`` extra var to specify the location of the backup file.

.. _ag_clustering_backup_restore:

Backup and Restore for Clustered Environments 
================================================

.. index::
   single: clustering; backup
   pair: clustering; restore

The procedure for backup and restore for a clustered environment is similar to a single install, except with some considerations described in this section. 

- If restoring to a new cluster, make sure the old cluster is shut down before proceeding because they could conflict with each other when accessing the database. 
- Per-node backups will only be restored to nodes bearing the same hostname as the backup.

When restoring to an existing cluster, the restore contains:

- Dump of the PostgreSQL database
- UI artifacts (included in database dump)
- Controller configuration (retrieved from ``/etc/tower``)
- Controller secret key
- Manual projects

.. _ag_clustering_backup_restore_diff_cluster:

Restoring to a different cluster
----------------------------------

When restoring a backup to a separate instance or cluster, manual projects and custom settings under /etc/tower are retained. Job output and job events are stored in the database, and therefore, not affected.

The restore process will not alter instance groups present before the restore (neither will it introduce any new instance groups). Restored controller resources that were associated to instance groups will likely need to be reassigned to instance groups present on the new controller cluster. 

