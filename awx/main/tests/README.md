## Test Environments

Several of the subfolders of `awx/main/tests/` indicate a different required _environment_
where you can run the tests. Those folders are:

 - `functional/` - requires a test database and no other services running
 - `live/` - must run in `tools_awx_1` container launched by `make docker-compose`
 - `unit/` - does not require a test database or any active services

### Functional and unit test environment

The functional and unit tests have an invocation in `make test`,
and this attaches several other things like schema that piggybacks on requests.
These tests are ran from the root AWX folder.

#### Functional tests

Only tests in the `functional/` folder should use the `@pytest.mark.django_db` decorator.
This is the only difference between the functional and unit folders,
the test environment is otherwise the same for both.

Functional tests use a sqlite3 database, so the postgres service is not necessary.

### Live tests

The live tests have an invocation in `make live_test` which will change
directory before running, which is required to pick up a different pytest
configuration.

This will use the postges container from `make docker-compose` for the database,
and will disable the pytest-django features of running with a test database
and running tests in transactions.
This means that any changes done in the course of the test could potentially
be seen in your browser via the API or UI, and anything the test fails
to clean up will remain in the database.

### Folders that should not contain tests

 - `data/` - just files other tests use
 - `docs/` - utilities for schema generation
 - `factories/` - general utilities
 - `manual/` - python files to be ran directly
