# How to test modules

To test, you need a running instance of Foreman, probably with Katello (use [forklift](https://github.com/theforeman/forklift) if unsure).
Also you need to run `make test-setup` and update `tests/test_playbooks/vars/server.yml`:

```sh
make test-setup
vi tests/test_playbooks/vars/server.yml # point to your Foreman instance
```

To run the tests using the `foreman_global_parameter` module as an example:

```sh
make test # all tests
make test_global_parameter  # single test
make test TEST="-k 'organzation or global_parameter'"  # select tests by expression (see `pytest -h`)
```

The tests are run against prerecorded server-responses.
You can (re-)record the cassettes for a specific test with

```sh
make record_global_parameter
```

# Guidedeline to writing tests

The tests in this repository run playbooks that can be found in `tests/test_playbooks`.
To be run, the name of the corresponding playbook must be listed in `tests/test_crud.py`.

The playbooks should be self contained, target the features of a specific module and be able to run against an actual foreman instance.
The structure would usually be something like setup -> run tests -> clean up.

In `tests/test_playbooks/tasks`, preconfigured tasks for individual entities / actions can be found.
They can be reused, to create common dependent resources, as well as to manipulate the entities in the actual test.
If the boolean variable `expected_change` is set, such a task fails if the result does not meet this expectation.

The ansible inventory contains two hosts:

- localhost: This host runs locally without modification it is meant to setup (and teardown) dependent resources, only when (re-)recording.
  It can also be useful to run ad hoc commands or small playbooks during development.
- tests: This host should run the actual tests. It is used to record the vcr-yaml-files, or to run isolated against those files.

In order to run these tests, the API responses of a running Foreman or Katello server must be recorded.
For this last step, `tests/test_playbooks/vars/server.yml` must be configured to point to a running Foreman or Katello server.
Then, `make record_<playbook name>` must be called, and the resulting vcr files (`test_playbook/fixtures/<playbook_name>-*.yml`) must be checked into git.

## Recording/storing apidoc.json for tests

Modules that use the `apypie` library depend on a valid `apidoc.json` being available during test execution.
The easiest way to do so is to provide a `<module>.json` in the `tests/fixtures/apidoc` folder.
Most modules can just use a symlink to either `foreman.json` or `katello.json`, depending on whether they need a plain Foreman or Foreman+Katello to function properly.
If you need a setup with different plugins enabled, just get `https://foreman.example.com/apidoc/v2.json` from your install and place it in `tests/fixtures/apidoc`.
