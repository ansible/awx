# Project data for live tests

Each folder in this directory is usable as source for a project or role or collection,
which is used in tests, particularly the "awx/main/tests/live" tests.

Although these are not git repositories, test fixtures will make copies,
and in the coppied folders, run `git init` type commands, turning them into
git repos. This is done in the locations

 - `/var/lib/awx/projects`
 - `/tmp/live_tests`

These can then be referenced for manual projects or git via the `file://` protocol.

## debug

This is the simplest possible case with 1 playbook with 1 debug task.

## with_requirements

This has a playbook that runs a task that uses a role.

The role project is referenced in the `roles/requirements.yml` file.

### role_requirement

This is the source for the role that the `with_requirements` project uses.

## test_host_query

This has a playbook that runs a task from a custom collection module which
is registered for the host query feature.

The collection is referenced in its `collections/requirements.yml` file.

### host_query

This can act as source code for a collection that enables host/event querying.

It has a `meta/event_query.yml` file, which may provide you an example of how
to implement this in your own collection.
