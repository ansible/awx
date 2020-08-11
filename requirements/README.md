# Dependency Management

The `requirements.txt` and `requirements_ansible.txt` files are generated from `requirements.in` and `requirements_ansible.in`, respectively, using `pip-tools` `pip-compile`.

## How To Use

Commands should be run from inside the `./requirements` directory of the awx repository.

Make sure you have `patch, awk, python3, python2, python3-venv, python2-virtualenv, pip2, pip3` installed. The development container image should have all these.

Even in the dev container, you may still have to dnf install `libpq-devel libcurl-devel`.

### Upgrading or Adding Select Libraries

If you need to add or upgrade one targeted library, then modify `requirements.in`,
then run the script:

`./updater.sh`

#### Upgrading Unpinned Dependency

If you require a new version of a dependency that does not have a pinned version
for a fix or feature, pin a minimum version and run `./updater.sh`. For example,
replace the line `asgi-amqp` with `asgi-amqp>=1.1.4`, and consider leaving a
note.

Then next time that a general upgrade is performed, the minimum version specifiers
can be removed, because `*.txt` files are upgraded to latest.

### Upgrading Dependencies

You can upgrade (`pip-compile --upgrade`) the dependencies by running

`./updater.sh upgrade`.

## What The Script Does

This script will:

  - Update `requirements.txt` based on `requirements.in`
  - Update/generate `requirements_ansible.txt` based on `requirements_ansible.in`
    - including an automated patch that adds `python_version < "3"` for Python 2 backward compatibility

## Licenses and Source Files

If any library has a change to its license with the upgrade, then the license for that library
inside of `docs/licenses` needs to be updated.

For libraries that have source distribution requirements (LGPL as an example),
a tarball of the library is kept along with the license.
To download the PyPI tarball, you can run this command:

```
pip download <pypi library name> -d docs/licenses/ --no-binary :all: --no-deps
```

Make sure to delete the old tarball if it is an upgrade.

## UPGRADE BLOCKERs

Anything pinned in `*.in` files involves additional manual work in
order to upgrade. Some information related to that work is outlined here.

### django

For any upgrade of Django, it must be confirmed that
we don't regress on FIPS support before merging.

See internal integration test knowledge base article `how_to_test_FIPS`
for instructions.

If operating in a FIPS environment, `hashlib.md5()` will raise a `ValueError`,
but will support the `usedforsecurity` keyword on RHEL and Centos systems.

Keep an eye on https://code.djangoproject.com/ticket/28401

The override of `names_digest` could easily be broken in a future version.
Check that the import remains the same in the desired version.

https://github.com/django/django/blob/af5ec222ccd24e81f9fec6c34836a4e503e7ccf7/django/db/backends/base/schema.py#L7

### social-auth-app-django

django-social keeps a list of backends in memory that it gathers
based on the value of `settings.AUTHENTICATION_BACKENDS` *at import time*:
https://github.com/python-social-auth/social-app-django/blob/c1e2795b00b753d58a81fa6a0261d8dae1d9c73d/social_django/utils.py#L13

Our `settings.AUTHENTICATION_BACKENDS` can *change*
dynamically as Tower settings are changed (i.e., if somebody
configures Github OAuth2 integration), so we need to
_overwrite_ this in-memory value at the top of every request so
that we have the latest version
see: https://github.com/ansible/tower/issues/1979

### django-oauth-toolkit

Version 1.2.0 of this project has a bug that error when revoking tokens.
This is fixed in the master branch but is not yet released.

When upgrading past 1.2.0 in the future, the `0025` migration needs to be
edited, just like the old migration was edited in the project:
https://github.com/jazzband/django-oauth-toolkit/commit/96538876d0d7ea0319ba5286f9bde842a906e1c5
The field can simply have the validator method `validate_uris` removed.

### azure-keyvault

Upgrading to 4.0.0 causes error because imports changed.

```
  File "/var/lib/awx/venv/awx/lib64/python3.6/site-packages/awx/main/credential_plugins/azure_kv.py", line 4, in <module>
  from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
ImportError: cannot import name 'KeyVaultClient'
```

### slackclient

Imports as used in `awx/main/notifications/slack_backend.py` changed
in version 2.0. This plugin code will need to change and be re-tested
as the upgrade takes place.

### django-jsonfield

Instead of calling a `loads()` operation, the returned value is casted into
a string in some cases, introduced in the change:

https://github.com/adamchainz/django-jsonfield/pull/14

This breaks a very large amount of AWX code that assumes these fields
are returned as dicts. Upgrading this library will require a refactor
to accomidate this change.

### wheel

azure-cli-core requires a version of wheel that is incompatible with
certain packages building with later versions of pip, so we override it.

### pip and setuptools

The offline installer needs to have functionality confirmed before upgrading these.
Versions need to match the versions used in the pip bootstrapping step
in the top-level Makefile.

## Library Notes

### pexpect

Version 4.8 makes us a little bit nervous with changes to `searchwindowsize` https://github.com/pexpect/pexpect/pull/579/files
Pin to `pexpect==4.7.x` until we have more time to move to `4.8` and test.

