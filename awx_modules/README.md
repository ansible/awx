# AWX Ansible Modules

These modules allow for easy interaction with an AWX or Ansible Tower server
in Ansible playbooks.

The previous home for these modules was in https://github.com/ansible/ansible
inside the folder `lib/ansible/modules/web_infrastructure/ansible_tower`.

## Running

To use these modules, the "old" tower-cli needs to be installed
in the virtual environment where the modules run.
You can install it from either:

 - https://github.com/ansible/tower-cli/
 - https://pypi.org/project/ansible-tower-cli/

To use these modules in AWX, you should create a custom virtual environment
to install the requirement into. NOTE: you will also probably still need
to set the job template extra_vars to include `ansible_python_interpreter`
to be the python in that virtual environment.

## Running Tests

Tests to verify compatibility with the most recent AWX code exist
in `awx_modules/test/awx`. These tests require that python packages
are available for all of `awx`, `ansible`, `tower_cli`, and the modules
themselves.

The target `make prepare_modules_venv` will prepare some requirements
in the `awx_modules_test_venv` folder so that `make test_modules` can
be ran to actually run the tests. A single test can be ran via:

```
make test_modules MODULE_TEST_DIRS=awx_modules/test/awx/test_organization.py
```

## Building

To build, you should not be in the AWX virtual environment.
This should work on any machine that has a sufficiently recent version
of Ansible installed.

```
cd awx_modules
ansible-galaxy build
```

This will leave a tar file in the awx_modules directory.

This process may be amended in the future to template components of `galaxy.yml`
from values (such as version) taken from AWX.
