
Execution Environment Setup Reference
=======================================

This section contains reference information associated with the definition of an |ee|.

You define the content of your execution environment in a YAML file. By default, this file is called ``execution_environment.yml``. This file tells Ansible Builder how to create the build instruction file (Containerfile for Podman, Dockerfile for Docker) and build context for your container image.

.. note::

  This page documents the definition schema for Ansible Builder 3.x. If you are running an older version of Ansible Builder, you need an older schema version. Please consult older versions of the docs for more information. We recommend using version 3, which offers substantially more configurable options and functionality than previous versions.

.. _ref_ee_definition:

Execution environment definition
---------------------------------

A definition file is a ``.yml`` file that is required to build an image for an |ee|. Below is a sample version 3 |ee| definition schema file. To use Ansible Builder 3.x, you must specify the schema version. If your |ee| file does not specify ``version: 3``, Ansible Builder will assume you want version 1. 

::

  ---
  version: 3

  build_arg_defaults:
    ANSIBLE_GALAXY_CLI_COLLECTION_OPTS: '--pre'

  dependencies:
    galaxy: requirements.yml
    python:
      - six
      - psutil
    system: bindep.txt

  images:
    base_image:
      name: registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel8:latest

  additional_build_files:
      - src: files/ansible.cfg
        dest: configs

  additional_build_steps:
    prepend_galaxy:
      - ADD _build/configs/ansible.cfg ~/.ansible.cfg

    prepend_final: |
      RUN whoami
      RUN cat /etc/os-release
    append_final:
      - RUN echo This is a post-install command!
      - RUN ls -la /etc


Configuration options
----------------------

You may use the configuration YAML keys listed here in your v3 |ee| definition file. The Ansible Builder 3.x execution environment definition file accepts seven top-level sections:

.. contents::
    :local:

additional_build_files
~~~~~~~~~~~~~~~~~~~~~~~

Specifies files to be added to the build context directory. These can then be referenced or copied by ``additional_build_steps`` during any build stage. The format is a list of dictionary values, each with a ``src`` and ``dest`` key and value. 

Each list item must be a dictionary containing the following (non-optional) keys:

**src**
  Specifies the source file(s) to copy into the build context directory. This may either be an absolute path (e.g., ``/home/user/.ansible.cfg``), or a path that is relative to the |ee| file. Relative paths may be a glob expression matching one or more files (e.g. ``files/*.cfg``). Note that an absolute path may **not** include a regular expression. If ``src`` is a directory, the entire contents of that directory are copied to ``dest``.

**dest**
  Specifies a subdirectory path underneath the ``_build`` subdirectory of the build context directory that should contain the source file(s) (e.g., ``files/configs``). This may not be an absolute path or contain ``..`` within the path. This directory will be created for you if it does not exist.

.. note::
  When using an ``ansible.cfg`` file to pass a token and other settings for a private account to an |ah| server, listing the config file path here (as a string) will enable it to be included as a build argument in the initial phase of the build.


additional_build_steps
~~~~~~~~~~~~~~~~~~~~~~~

Specifies custom build commands for any build phase. These commands will be inserted directly into the build instruction file for the container runtime (e.g., Containerfile or Dockerfile). The commands must conform to any rules required by the containerization tool.

You can add build steps before or after any stage of the image creation process. For example, if you need ``git`` to be installed before you install your dependencies, you can add a build step at the end of the base build stage.

Below are the valid keys for this section. Each supports either a multi-line string, or a list of strings.

**prepend_base**
  Commands to insert before building of the base image.

**append_base**
  Commands to insert after building of the base image.

**prepend_galaxy**
  Commands to insert before building of the galaxy image.

**append_galaxy**
  Commands to insert after building of the galaxy image.

**prepend_builder**
  Commands to insert before building of the builder image.

**append_builder**
  Commands to insert after building of the builder image.

**prepend_final**
  Commands to insert before building of the final image.

**append_final**
  Commands to insert after building of the final image.


build_arg_defaults
~~~~~~~~~~~~~~~~~~~
Specifies default values for build args as a dictionary. This is an alternative to using the ``--build-arg`` CLI flag.

Build arguments used by ``ansible-builder`` are the following:

**ANSIBLE_GALAXY_CLI_COLLECTION_OPTS** 
  Allows the user to pass the ``–pre`` flag (or others) to enable the installation of pre-release collections.

**ANSIBLE_GALAXY_CLI_ROLE_OPTS**
  This allows the user to pass any flags, such as --no-deps, to the role installation.

**PKGMGR_PRESERVE_CACHE**
  This controls how often the package manager cache is cleared during the image build process. If this value is not set, which is the default, the cache is cleared frequently. If it is set to the string ``always``, the cache is never cleared. Any other value forces the cache to be cleared only after the system dependencies are installed in the final build stage.

Ansible Builder hard-codes values given inside of ``build_arg_defaults`` into the build instruction file, so they will persist if you run your container build manually.

If you specify the same variable in the |ee| definition and at the command line with the CLI ``build-arg`` flag, the CLI value will take higher precedence (the CLI value will override the value in the |ee| definition).

.. _ref_collections_metadata:

dependencies
~~~~~~~~~~~~~

Specifies dependencies to install into the final image, including ``ansible-core``, ``ansible-runner``, Python packages, system packages, and Ansible Collections. Ansible Builder automatically installs dependencies for any Ansible Collections you install.

In general, you can use standard syntax to constrain package versions. Use the same syntax you would pass to ``dnf``, ``pip``, ``ansible-galaxy``, or any other package management utility. You can also define your packages or collections in separate files and reference those files in the ``dependencies`` section of your |ee| definition file.

The following keys are valid for this section:

**ansible_core**
  The version of the ``ansible-core`` Python package to be installed. This value is a dictionary with a single key, ``package_pip``. The ``package_pip`` value is passed directly to pip for installation and can be in any format that pip supports. Below are some example values:
  ::

    ansible_core:
        package_pip: ansible-core
    ansible_core:
        package_pip: ansible-core==2.14.3
    ansible_core:
        package_pip: https://github.com/example_user/ansible/archive/refs/heads/ansible.tar.gz

**ansible_runner**
  The version of the Ansible Runner Python package to be installed. This value is a dictionary with a single key, package_pip. The package_pip value is passed directly to pip for installation and can be in any format that pip supports. Below are some example values:
  ::

    ansible_runner:
        package_pip: ansible-runner
    ansible_runner:
        package_pip: ansible-runner==2.3.2
    ansible_runner:
        package_pip: https://github.com/example_user/ansible-runner/archive/refs/heads/ansible-runner.tar.gz


**galaxy**
  Ansible Collections to be installed from Galaxy. This may be a filename, a dictionary, or a multi-line string representation of an Ansible Galaxy ``requirements.yml`` file (see below for examples). Read more about the requirements file format in the `Galaxy user guide <https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#install-multiple-collections-with-a-requirements-file>`_.

**python**
  The Python installation requirements. This may either be a filename, or a list of requirements (see below for an example). Ansible Builder combines all the Python requirements files from all collections into a single file using the ``requirements-parser`` library. This library supports complex syntax, including references to other files. If multiple collections require the same *package name*, Ansible Builder combines them into a single entry and combines the constraints. Certain package names are specifically *ignored* by ``ansible-builder``, meaning that Ansible Builder does not include them in the combined file of Python dependencies, even if a collection lists them as dependencies. These include test packages and packages that provide Ansible itself. The full list can be found in ``EXCLUDE_REQUIREMENTS`` in ``src/ansible_builder/_target_scripts/introspect.py``. If you need to include one of these ignored package names, use the ``--user-pip`` option of the ``introspect`` command to list it in the user requirements file. Packages supplied this way are not processed against the list of excluded Python packages.

**python_interpreter**
  A dictionary that defines the Python system package name to be installed by dnf (``package_system``) and/or a path to the Python interpreter to be used (``python_path)``.

**system**
  The system packages to be installed, in bindep format. This may either be a filename, or a list of requirements (see below for an example). For more information about bindep, refer to the `OpenDev documentation <https://docs.opendev.org/opendev/bindep/latest/readme.html>`_.
  For system packages, use the ``bindep`` format to specify cross-platform requirements, so they can be installed by whichever package management system the execution environment uses. Collections should specify necessary requirements for ``[platform:rpm]``. Ansible Builder combines system package entries from multiple collections into a single file. Only requirements with *no* profiles (runtime requirements) are installed to the image. Entries from multiple collections which are outright duplicates of each other may be consolidated in the combined file. 

The following example uses filenames that contain the various dependencies:

  ::

    dependencies:
      python: requirements.txt
      system: bindep.txt
      galaxy: requirements.yml
      ansible_core:
          package_pip: ansible-core==2.14.2
      ansible_runner:
          package_pip: ansible-runner==2.3.1
      python_interpreter:
          package_system: "python310"
          python_path: "/usr/bin/python3.10"

And this example uses inline values:

  ::

    dependencies:
      python:
        - pywinrm
      system:
        - iputils [platform:rpm]
      galaxy:
        collections:
          - name: community.windows
          - name: ansible.utils
            version: 2.10.1
      ansible_core:
          package_pip: ansible-core==2.14.2
      ansible_runner:
          package_pip: ansible-runner==2.3.1
      python_interpreter:
          package_system: "python310"
          python_path: "/usr/bin/python3.10"


.. note::

  If any of these dependency files (``requirementa.txt,bindep.txt, and requirements.yml``) are in the ``build_ignore`` of the collection, it will not work correctly.

  Collection maintainers can verify that ansible-builder recognizes the requirements they expect by using the ``introspect`` command, for example:

  ::

    ansible-builder introspect --sanitize ~/.ansible/collections/

The ``--sanitize`` option reviews all of the collection requirements and removes duplicates. It also removes any Python requirements that should normally be excluded. Use the ``-v3`` option to ``introspect`` to see logging messages about requirements that are being excluded. 


images
~~~~~~~

Specifies the base image to be used. At a minimum you **MUST** specify a source, image, and tag for the base image. The base image provides the operating system and may also provide some packages. We recommend using the standard ``host/namespace/container:tag`` syntax to specify images. You may use Podman or Docker shortcut syntax instead, but the full definition is more reliable and portable.

Valid keys for this section are:

**base_image**
  A dictionary defining the parent image for the execution environment. A ``name`` key must be supplied with the container image to use. Use the ``signature_original_name`` key if the image is mirrored within your repository, but signed with the original image's signature key.

image verification
^^^^^^^^^^^^^^^^^^^
You can verify signed container images if you are using the ``podman`` container runtime. Set the ``container-policy`` CLI option to control how this data is used in relation to a Podman ``policy.json`` file for container image signature validation.

- ``ignore_all`` policy: Generate a ``policy.json`` file in the build ``context directory <context>`` where no signature validation is performed.
- ``system`` policy: Signature validation is performed using pre-existing ``policy.json`` files in standard system locations. ``ansible-builder`` assumes no responsibility for the content within these files, and the user has complete control over the content.
- ``signature_required`` policy: ``ansible-builder`` will use the container image definitions here to generate a ``policy.json`` file in the build ``context directory <context>`` that will be used during the build to validate the images.


options
~~~~~~~~

A dictionary of keywords/options that can affect builder runtime functionality. Valid keys for this section are:

**container_init**
  A dictionary with keys that allow for customization of the container ``ENTRYPOINT`` and ``CMD`` directives (and related behaviors). Customizing these behaviors is an advanced task, and may result in subtle, difficult-to-debug failures. As the provided defaults for this section control a number of intertwined behaviors, overriding any value will skip all remaining defaults in this dictionary. Valid keys are:

  **cmd**
    Literal value for the ``CMD`` Containerfile directive. The default value is ``["bash"]``.

  **entrypoint**
    Literal value for the ``ENTRYPOINT`` Containerfile directive. The default entrypoint behavior handles signal propagation to subprocesses, as well as attempting to ensure at runtime that the container user has a proper environment with a valid writeable home directory, represented in ``/etc/passwd``, with the ``HOME`` environment variable set to match. The default entrypoint script may emit warnings to ``stderr`` in cases where it is unable to suitably adjust the user runtime environment. This behavior can be ignored or elevated to a fatal error; consult the source for the ``entrypoint`` target script for more details. The default value is ``["/opt/builder/bin/entrypoint", "dumb-init"]``.

  **package_pip**
    Package to install via pip for entrypoint support. This package will be installed in the final build image. The default value is ``dumb-init==1.2.5``.

**package_manager_path**
  A string with the path to the package manager (dnf or microdnf) to use. The default is ``/usr/bin/dnf``. This value will be used to install a Python interpreter, if specified in ``dependencies``, and during the build phase by the ``assemble`` script.

**skip_ansible_check**
  This boolean value controls whether or not the check for an installation of Ansible and Ansible Runner is performed on the final image. Set this value to ``True`` to not perform this check. The default is ``False``.

**relax_passwd_permissions**
  This boolean value controls whether the ``root`` group (GID 0) is explicitly granted write permission to ``/etc/passwd`` in the final container image. The default entrypoint script may attempt to update ``/etc/passwd`` under some container runtimes with dynamically created users to ensure a fully-functional POSIX user environment and home directory. Disabling this capability can cause failures of software features that require users to be listed in ``/etc/passwd`` with a valid and writeable home directory (eg, ``async`` in ansible-core, and the ``~username`` shell expansion). The default is ``True``.

**workdir**
  Default current working directory for new processes started under the final container image. Some container runtimes also use this value as ``HOME`` for dynamically-created users in the ``root`` (GID 0) group. When this value is specified, the directory will be created (if it doesn't already exist), set to ``root`` group ownership, and ``rwx`` group permissions recursively applied to it. The default value is ``/runner``.

**user**
  This sets the username or UID to use as the default user for the final container image. The default value is ``1000``.

Example options section:
::

  options:
      container_init:
          package_pip: dumb-init>=1.2.5
          entrypoint: '["dumb-init"]'
          cmd: '["csh"]'
      package_manager_path: /usr/bin/microdnf
      relax_password_permissions: false
      skip_ansible_check: true
      workdir: /myworkdir
      user: bob


version
~~~~~~~~

An integer value that sets the schema version of the execution environment definition file. Defaults to ``1``. Must be ``3`` if you are using Ansible Builder 3.x.


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
