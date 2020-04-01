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


 - When a project is created, it will wait for the update/sync to finish by default; this can be turned off with the `wait` parameter, if desired.
 - Creating a "scan" type job template is no longer supported.
 - Specifying a custom certificate via the `TOWER_CERTIFICATE` environment variable no longer works.
 - Type changes of variable fields
   - `extra_vars` in the `tower_job_launch` module worked with a `list` previously, but now only works with a `dict` type.
   - `extra_vars` in the `tower_workflow_job_template` module worked with a `string` previously but now expects a `dict`.
   - When the `extra_vars` parameter is used with the `tower_job_launch` module, the launch will fail unless `ask_extra_vars` or `survey_enabled` is explicitly set to `True` on the Job Template.
   - The `variables` parameter in the `tower_group`, `tower_host` and `tower_inventory` modules now expects a `dict` type and no longer supports the use of `@` syntax for a file.
 - Type changes of other types of fields
   - `inputs` or `injectors` in the `tower_credential_type` module worked with a string previously but now expects a `dict`.
   - `schema` in the `tower_workflow_job_template` module worked with a `string` previously but not expects a `list` of `dict`s.
 - `tower_group` used to also service inventory sources, but this functionality has been removed from this module; use `tower_inventory_source` instead.
 - Specified `tower_config` file used to handle `k=v` pairs on a single line; this is no longer supported. Please use a file formatted as `yaml`, `json` or `ini` only.
 - Some return values (e.g., `credential_type`) have been removed. Use of `id` is recommended.
 - `tower_job_template` no longer supports the deprecated `extra_vars_path` parameter, please use `extra_vars` with the lookup plugin to replace this functionality.

## Running Unit Tests

Tests to verify compatibility with the most recent AWX code are in `awx_collection/test/awx`.
These can be ran by `make test_collection` in the development container.

To run outside of the development container, or to run against
Ansible or `tower-cli` source, set up a working environment:

```
mkvirtualenv my_new_venv
# may need to replace psycopg2 with psycopg2-binary in requirements/requirements.txt
pip install -r requirements/requirements.txt -r requirements/requirements_dev.txt -r requirements/requirements_git.txt
make clean-api
pip install -e <path to your Ansible>
pip install -e .
py.test awx_collection/test/awx/
```

If you do not install tower-cli, it will skip tests for modules that require it.

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
