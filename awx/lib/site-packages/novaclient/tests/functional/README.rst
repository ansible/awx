=====================================
python-novaclient functional testing
=====================================

Idea
------

Over time we have noticed two issues with novaclient unit tests.

* Does not exercise the CLI
* We can get the expected server behavior wrong, and test the wrong thing.

We are using functional tests, run against a running cloud
(primarily devstack), to address these two cases.

Additionally these functional tests can be considered example uses
of python-novaclient.

These tests started out in tempest as read only nova CLI tests, to make sure
the CLI didn't simply stacktrace when being used (which happened on
multiple occasions).


Testing Theory
----------------

We are treating python-novaclient as legacy code, so we do not want to spend a
lot of effort adding in missing features. In the future the CLI will move to
python-openstackclient, and the python API will be based on the OpenStack
SDK project. But until that happens we still need better functional testing,
to prevent regressions etc.


Since python-novaclient has two uses, CLI and python API, we should have two
sets of functional tests. CLI and python API. The python API tests should
never use the CLI. But the CLI tests can use the python API where adding
native support to the CLI for the required functionality would involve a
non trivial amount of work.

Functional Test Guidelines
---------------------------

* Consume credentials via standard client environmental variables::

    OS_USERNAME
    OS_PASSWORD
    OS_TENANT_NAME
    OS_AUTH_URL

* Try not to require an additional configuration file
