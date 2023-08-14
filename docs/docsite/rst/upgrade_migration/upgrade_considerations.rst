
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

   All upgrades should be no more than two major versions behind what you are currently upgrading to. For example, in order to upgrade to |at| 4.3, you must first be on version 4.1.x; i.e., there is no direct upgrade path from version 3.8.x or earlier.

   In order to run |at| 4.3, you must also have Ansible 2.12 at minimum.

.. _upgrade_planning:

Upgrade Planning
------------------

This section covers changes that you should keep in mind as you attempt to upgrade your |at| instance.

- Clustered upgrades require special attention to instance and instance groups prior to starting the upgrade. See `:ref:`ag_clustering` for details.


Running the Setup Playbook
----------------------------

.. include:: ../common/setup-playbook.rst    

