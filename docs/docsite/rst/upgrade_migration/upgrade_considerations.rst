
.. FROM NOTES:      short intro to setup script; doc differences; answers file in new format in inventory

Upgrading to Ansible Automation Platform
========================================

.. index::
    single: upgrade considerations
    single: upgrade

|ah| acts as a content provider for |at|, which requires both an |at| deployment and an |ah| deployment running alongside each other. The |aap| installer contains both of these. This section covers each component of the upgrading process:

.. contents::
    :local:

.. note::

   All upgrades should be no more than two major versions behind what you are currently upgrading to. For example, in order to upgrade to |at| 4.3, you must first be on version 4.1.x; i.e., there is no direct upgrade path from version 3.8.x or earlier. Refer to the `recommended upgrade path article <https://access.redhat.com/articles/4098921>`_ on the Red Hat customer portal. 
   
   In order to run |at| 4.3, you must also have Ansible 2.12 at minimum. 

To help you determine the right upgrade or migration path when moving from an old |aap| or Tower version to a new |aap| version, use the Upgrade Assistant at https://access.redhat.com/labs/aapua/. If prompted, use your Red Hat customer credentials to login.

.. _upgrade_planning:

Upgrade Planning 
------------------

This section covers changes that you should keep in mind as you attempt to upgrade your |at| instance.

- Even if you already have a valid license from a previous version, you must still provide your credentials or a subscriptions manifest again upon upgrading to the latest automation controller. See :ref:`import_subscription` in the |atu|.
- If you need to upgrade |rhel| and |at|, you will need to do a backup and restore of your controller data (from the automation controller). Refer to :ref:`ag_backup_restore` in the |ata| for further detail.
- Clustered upgrades require special attention to instance and instance groups prior to starting the upgrade. See `Editing the Red Hat Ansible Automation Platform installer inventory file <https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/2.2/html/red_hat_ansible_automation_platform_installation_guide/single-machine-scenario#editing_the_red_hat_ansible_automation_platform_installer_inventory_file>`_ and :ref:`ag_clustering` for details.


Obtaining the Installer
-------------------------

Refer to `Choosing and obtaining a Red Hat Ansible Automation Platform installer <https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/2.2/html-single/red_hat_ansible_automation_platform_installation_guide/index#choosing_and_obtaining_a_red_hat_ansible_automation_platform_installer>`_ on the `Red Hat Customer Portal <https://access.redhat.com/>`_ for detail. Be sure to use your Red Hat customer login to access the full content.


Setting up the Inventory File
--------------------------------

See `Editing the Red Hat Ansible Automation Platform installer inventory file <https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/2.2/html/red_hat_ansible_automation_platform_installation_guide/single-machine-scenario#editing_the_red_hat_ansible_automation_platform_installer_inventory_file>`_ for information.

You can also automatically generate an inventory file based on your selections using a utility called the Inventory File Generator, which you can access at https://access.redhat.com/labs/aapifg/. If prompted, use your Red Hat customer credentials to login. 


Running the Setup Playbook
----------------------------

.. include:: ../common/setup-playbook.rst    

