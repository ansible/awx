## Collection tools

Tools used for building, maintaining, and testing the collection.

### Template Galaxy

The `template_galaxy.yml` playbook ran as a pre-requisite for building the collection.

```
make awx_collection_build
```

### Generate

This will template resource modules (like `group`, for groups in inventory) from a boilerplate template.
It is intended as a tool for writing new modules or enforcing consistency.

### Integration Testing

These instructions assume you have ansible-core and the collection installed.
To install the collection in-place (to pick up any local changes to source)
the `make symlink_collection` will simlink the `awx_collection/` folder to
the appropriate place under `~/.ansible/collections`.

This is a shortcut for quick validation of tests that bypasses `ansible-test`.

Authentication is automatically set up using the admin_password secret.
This might stop working if you delete the `tools/docker-compose/_sources` folder.

To run some sample modules:

```
ansible-playbook -i localhost, awx_collection/tools/integration_testing.yml
```

To run just one module (the most common use case), use the `-e test=<name>`.

```
ansible-playbook -i localhost, awx_collection/tools/integration_testing.yml -e test=host
```

If you want to run _all_ the tests, then you need to pass in the whole list.
This will take significant time and is not ideal from an error-handling perspective,
but this is a way to do it:

```
ansible-playbook -i localhost, awx_collection/tools/integration_testing.yml -e test=$(ls -1Am awx_collection/tests/integration/targets/ | tr -d '[:space:]')
```

Depending on the module, you may need special dependencies.
For instance, the rrule lookup plugins need `pytz`.
These will be satisfied if you install requirements in `awx_collection/requirements.txt`.
