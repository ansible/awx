# AWX Ansible Collection

This Ansible collection allows for easy interaction with an AWX or Ansible Tower
server via Ansible playbooks.

The previous home for this collection was in https://github.com/ansible/ansible
inside the folder `lib/ansible/modules/web_infrastructure/ansible_tower`
as well as other folders for the inventory plugin, module utils, and
doc fragment.

## Building and Installing

This collection templates the `galaxy.yml` file it uses.
Run `make build_collection` from the root folder of the AWX source tree.
This will create the `tar.gz` file inside the `awx_collection` folder
with the current AWX version, for example: `awx_collection/awx-awx-9.2.0.tar.gz`.

Installing the `tar.gz` involves no special instructions.

## Running

Modules in this collection may have any of the following python requirements:

 - the official [AWX CLI](https://docs.ansible.com/ansible-tower/latest/html/towercli/index.html)
 - the deprecated `tower-cli` [PyPI](https://pypi.org/project/ansible-tower-cli/)
 - no requirements

See requirements in the `DOCUMENTATION` string specific to each module.

## Release and Upgrade Notes

The release 7.0.0 of the `awx.awx` collection is intended to be identical
to the content prior to the migration, aside from changes necessary to
have it function as a collection.

The following notes are changes that may require changes to playbooks:

 - Specifying `inputs` or `injectors` as strings in the
   `tower_credential_type` module is no longer supported. Provide them as dictionaries instead.
 - When a project is created, it will wait for the update/sync to finish by default; this can be turned off with the `wait` parameter, if desired.
 - Creating a "scan" type job template is no longer supported.
 - `extra_vars` in the `tower_job_launch` module worked with a list previously, but is now configured to work solely in a `dict` format.
 - When the `extra_vars` parameter is used with the `tower_job_launch` module, the Job Template launch will fail unless `add_extra_vars` or `survey_enabled` is explicitly set to `True` on the Job Template.
 - `tower_group` used to also service inventory sources, but this functionality has been removed from this module; use `tower_inventory_source` instead.
 - Specified `tower_config` file used to handle `k=v` pairs on a single line; this is no longer supported. Please use a file formatted as `yaml`, `json` or `ini` only.
 - The `variables` parameter in the `tower_group`, `tower_host` and `tower_inventory` modules are now in `dict` format and no longer supports the use of the `C(@)` syntax (for an external `vars` file).
 - Some return values (e.g., `credential_type`) have been removed. Use of `id` is recommended.

## Running Unit Tests

Tests to verify compatibility with the most recent AWX code are
in `awx_collection/test/awx`. These tests require that Python packages
are available for all of `awx`, `ansible`, `tower_cli`, and the collection
itself.

### Inside Development Container

The target `make prepare_collection_venv` will prepare some requirements
in the `awx_collection_test_venv` folder so that `make test_collection` can
be executed to actually run the tests. A single test can be run via:

```
make test_collection COLLECTION_TEST_DIRS=awx_collection/test/awx/test_organization.py
```

### Manually

As a faster alternative (if you do not want to use the container), or to
run against Ansible or `tower-cli` source, it is possible to set up a
working environment yourself:

```
mkvirtualenv my_new_venv
# may need to replace psycopg2 with psycopg2-binary in requirements/requirements.txt
pip install -r requirements/requirements.txt -r requirements/requirements_dev.txt -r requirements/requirements_git.txt
make clean-api
pip install -e <path to your Ansible>
pip install -e <path to your tower-cli>
pip install -e .
PYTHONPATH=awx_collection:$PYTHONPATH py.test awx_collection/test/awx/
```

## Running Integration Tests

The integration tests require a virtualenv with `ansible` >= 2.9 and `tower_cli`.
The collection must first be installed, which can be done using `make install_collection`.
You also need a configuration file at `~/.tower_cli.cfg` or
`/etc/tower/tower_cli.cfg` with the credentials for accessing tower. This can
be populated using `tower-cli`:

```
tower-cli config host $HOST
tower-cli config username $USERNAME
tower-cli config password $PASSWORD
# This tells the tower-cli not to veriffy the ssl certs in the tower, if your tower has good certs you should leave this to true
tower-cli config verify_ssl false
```

Finally you can run the tests:

```
# ansible-test must be run from the directory in which the collection is installed
cd ~/.ansible/collections/ansible_collections/awx/awx/
ansible-test integration
```

## Licensing

All content in this folder is licensed under the same license as Ansible,
which is the same as license that applied before the split into an
independent collection.
