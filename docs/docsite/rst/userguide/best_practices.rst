Best Practices
--------------

.. index::
   single: best practices

Use Source Control
~~~~~~~~~~~~~~~~~~

.. index::
   pair: best practices; source control

While AWX supports playbooks stored directly on the server, best practice is to store your playbooks, roles, and any associated details in source control. This way you have an audit trail describing when and why you changed the rules that are automating your infrastructure. Plus, it allows for easy sharing of playbooks with other parts of your infrastructure or team.

Ansible file and directory structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: best practices; file and directory structure

Please review the `Ansible Tips and Tricks <https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html>`_ from the Ansible documentation. If creating a common set of roles to use across projects, these should be accessed via source control submodules, or a common location such as ``/opt``. Projects should not expect to import roles or content from other projects.

.. note::
    Playbooks should not use the ``vars_prompt`` feature, as AWX does not interactively allow for ``vars_prompt`` questions. If you must use ``vars_prompt``, refer to and make use of the :ref:`ug_surveys` functionality.

.. note::
    Playbooks should not use the ``pause`` feature of Ansible without a timeout, as AWX does not allow for interactively cancelling a pause. If you must use ``pause``, ensure that you set a timeout.

Jobs run use the playbook directory as the current working
directory, although jobs should be coded to use the ``playbook_dir``
variable rather than relying on this.

Use Dynamic Inventory Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: best practices; dynamic inventory sources

If you have an external source of truth for your infrastructure, whether it is a cloud provider or a local CMDB, it is best to define an inventory sync process and use the support for dynamic inventory (including cloud inventory sources). This ensures your inventory is always up to date.

.. include:: ../common/overwrite_var_note_2-4-0.rst

Variable Management for Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: best practices; variable inventory management

Keeping variable data along with the hosts and groups definitions (see the inventory
editor) is encouraged, rather than using ``group_vars/`` and
``host_vars/``. If you use dynamic inventory sources, AWX can sync
such variables with the database as long as the **Overwrite Variables**
option is not set.

Autoscaling
~~~~~~~~~~~~

.. index::
   pair: best practices; autoscaling

Using the "callback" feature to allow newly booting instances to request
configuration is very useful for auto-scaling scenarios or provisioning
integration.

Larger Host Counts
~~~~~~~~~~~~~~~~~~

.. index::
   pair: best practices; host counts, larger

Consider setting "forks" on a job template to larger values to increase
parallelism of execution runs. For more information on tuning Ansible,
see `the Ansible
blog <http://www.ansible.com/blog/ansible-performance-tuning>`__.

Continuous integration / Continuous Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: best practices; integration, continuous
   pair: best practices; deployment, continuous

For a Continuous Integration system, such as Jenkins, to spawn a job, it should make a curl request to a job template. The credentials to the job template should not require prompting for any particular passwords. Refer to the `CLI documentation`_ for configuration and usage instructions.

  .. _`CLI documentation`: https://docs.ansible.com/automation-controller/latest/html/controllercli/usage.html
