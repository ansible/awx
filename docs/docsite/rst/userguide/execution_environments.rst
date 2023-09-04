.. _ug_execution_environments:

Execution Environments
======================

.. index::
   single: execution environment
   pair: add; execution environment
   pair: jobs; add execution environment


.. include:: ../common/execution_environs.rst

.. _ug_build_ees:

Building an Execution Environment
---------------------------------

.. index::
    single: execution environment
    pair: build; execution environment


Using Ansible content that depends on non-default dependencies (custom virtual environments) can be tricky. Packages must be installed on each node, play nicely with other software installed on the host system, and be kept in sync. Previously, jobs ran inside of a virtual environment at ``/var/lib/awx/venv/ansible`` by default, which was pre-loaded with dependencies for ansible-runner and certain types of Ansible content used by the Ansible control machine. 

To help simplify this process, container images can be built that serve as Ansible `control nodes <https://docs.ansible.com/ansible/latest/network/getting_started/basic_concepts.html#control-node>`_. These container images are referred to as automation |ees|, which you can create with ansible-builder and then ansible-runner can make use of those images. 

Install ansible-builder
~~~~~~~~~~~~~~~~~~~~~~~~

In order to build images, either installations of podman or docker is required along with the ansible-builder Python package. The ``--container-runtime`` option needs to correspond to the Podman/Docker executable you intend to use.

Refer to the latest `Quickstart for Ansible Builder <https://ansible.readthedocs.io/projects/builder/en/latest/#quickstart-for-ansible-builder>`_ for detail.

.. _build_ee:

Build an execution environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ansible-builder is used to create an |ee|. 

An |ee| is expected to contain:

- Ansible
- Ansible Runner
- Ansible Collections
- Python and/or system dependencies of:

  - modules/plugins in collections
  - content in ansible-base
  - custom user needs

Building a new |ee| involves a definition (a ``.yml`` file) that specifies which content you would like to include in your |ee|, such as collections, Python requirements, and system-level packages. The content from the output generated from migrating to |ees| has some of the required data that can be piped to a file or pasted into this definition file.


Run the builder
~~~~~~~~~~~~~~~~

Once you created a definition, use this procedure to build your |ee|.

The ``ansible-builder build`` command takes an |ee| definition as an input. It outputs the build context necessary for building an |ee| image, and proceeds with building that image. The image can be re-built with the build context elsewhere, and produces the same result. By default, it looks for a file named ``execution-environment.yml`` in the current directory.

For the illustration purposes, the following example ``execution-environment.yml`` file is used as a starting point:

::

	---
	version: 3
	dependencies:
	  galaxy: requirements.yml

The content of ``requirements.yml``:

::

	---
	collections:
	  - name: awx.awx

To build an |ee| using the files above, run:

::	

	$ ansible-builder build
	...
	STEP 7: COMMIT my-awx-ee
	--> 09c930f5f6a
	09c930f5f6ac329b7ddb321b144a029dbbfcc83bdfc77103968b7f6cdfc7bea2
	Complete! The build context can be found at: context

In addition to producing a ready-to-use container image, the build context is preserved, which can be rebuilt at a different time and/or location with the tooling of your choice, such as ``docker build`` or ``podman build``.

For additional information about the ``ansible-builder build`` command, refer to Ansible's `CLI Usage <https://ansible.readthedocs.io/projects/builder/en/latest/usage/#cli-usage>`_ documentation.

Use an execution environment in jobs
------------------------------------

In order to use an |ee| in a job, a few components are required:

- An |ee| must have been created using |ab|. See :ref:`build_ee` for detail. Once an |ee| is created, you can use it to run jobs. Use the AWX user interface to specify the |ee| to use in your job templates.

- Depending on whether an |ee| is made available for global use or tied to an organization, you must have the appropriate level of administrator privileges in order to use an |ee| in a job. |Ees| tied to an organization require Organization administrators to be able to run jobs with those |ees|.

- Before running a job or job template that uses an |ee| that has a credential assigned to it, be sure that the credential contains a username, host, and password.

1. Click **Execution Environments** from the left navigation bar of the AWX user interface. 

2. Add an |ee| by selecting the **Add** button.

3. Enter the appropriate details into the following fields:

-  **Name**: Enter a name for the |ee| (required).
-  **Image**: Enter the image name (required). The image name requires its full location (repo), the registry, image name, and version tag in the example format of ``quay.io/ansible/awx-ee:latestrepo/project/image-name:tag``. 
-  **Pull**: optionally choose the type of pull when running jobs:

  - **Always pull container before running**: Pulls the latest image file for the container.
  - **Only pull the image if not present before running**: Only pulls latest image if none specified.
  - **Never pull container before running**: Never pull the latest version of the container image.

-  **Description**: optional.
-  **Organization**: optionally assign the organization to specifically use this |ee|. To make the |ee| available for use across multiple organizations, leave this field blank.
-  **Registry credential**: If the image has a protected container registry, provide the credential to access it.

.. image:: ../common/images/ee-new-ee-form-filled.png

4. Click **Save**. 

Now your newly added |ee| is ready to be used in a job template. To add an |ee| to a job template, specify it in the **Execution Environment** field of the job template, as shown in the example below. For more information on setting up a job template, see :ref:`ug_JobTemplates` in the |atu|.

.. image:: ../common/images/job-template-with-example-ee-selected.png

Once you added an |ee| to a job template, you can see those templates listed in the **Templates** tab of the |ee|:

.. image:: ../common/images/ee-details-templates-list.png


Execution environment mount options
-----------------------------------

.. index:: 
   pair: mount options; execution environment
   pair: system trust store; execution environment

.. https://github.com/ansible/product-docs/issues/1647 and https://github.com/ansible/awx/issues/10787

Rebuilding an |ee| is one way to add certs, but inheriting certs from the host provides a more convenient solution.  

Additionally, you may customize |ee| mount options and mount paths in the **Paths to expose to isolated jobs** field of the Job Settings page, where it supports podman-style volume mount syntax. Refer to the `Podman documentation <https://docs.podman.io/en/latest/markdown/podman-run.1.html#volume-v-source-volume-host-dir-container-dir-options>`_ for detail.

In some cases where the ``/etc/ssh/*`` files were added to the |ee| image due to customization of an |ee|, an SSH error may occur. For example, exposing the ``/etc/ssh/ssh_config.d:/etc/ssh/ssh_config.d:O`` path allows the container to be mounted, but the ownership permissions are not mapped correctly. 

If you encounter this error, or have upgraded from an older version of AWX, perform the following steps:

1. Change the container ownership on the mounted volume  to ``root``.

2. In the **Paths to expose to isolated jobs** field of the Job Settings page, using the current example, expose the path as such:

.. image:: ../common/images/settings-paths2expose-iso-jobs.png

.. note::

	The ``:O`` option is only supported for directories. It is highly recommended that you be as specific as possible, especially when specifying system paths. Mounting ``/etc`` or ``/usr`` directly have impact that make it difficult to troubleshoot. 

This informs podman to run a command similar to the example below, where the configuration is mounted and the ``ssh`` command works as expected.

::

	podman run -v /ssh_config:/etc/ssh/ssh_config.d/:O ...


.. https://github.com/ansible/awx/issues/11600

To expose isolated paths in OpenShift or Kubernetes containers as HostPath, assume the following configuration:

.. image:: ../common/images/settings-paths2expose-iso-jobs-mount-containers.png

Use the **Expose host paths for Container Groups** toggle to enable it. 

Once the playbook runs, the resulting Pod spec will display similar to the example below. Note the details of the ``volumeMounts`` and ``volumes`` sections.

.. image:: ../common/images/mount-containers-playbook-run-podspec.png

