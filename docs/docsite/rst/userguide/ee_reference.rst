
Execution Environment Setup Reference
=======================================

For detailed information about the |ee| definition,
refer to the `Ansible Builder documentation <https://ansible.readthedocs.io/projects/builder/en/latest/definition/#execution-environment-definition>`_.

Default execution environment for AWX
--------------------------------------

The example in ``test/data/pytz`` requires the ``awx.awx`` collection in the |ee| definition. The lookup plugin ``awx.awx.tower_schedule_rrule`` requires the PyPI ``pytz`` and another library to work. If ``test/data/pytz/execution-environment.yml`` file is provided to the ``ansible-builder build`` command, then it will install the collection inside the image, read the ``requirements.txt`` file inside of the collection, and then install ``pytz`` into the image.

The image produced can be used inside of an ``ansible-runner`` project by placing these variables inside the ``env/settings`` file, inside of the private data directory.

::

	---
	container_image: image-name
	process_isolation_executable: podman # or docker
	process_isolation: true

The ``awx.awx`` collection is a subset of content included in the default AWX |ee|. More details can be found in the `awx-ee repository <https://github.com/ansible/awx-ee>`_.
