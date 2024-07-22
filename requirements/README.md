# Dependency Management

The `requirements.txt` file is generated from `requirements.in` and `requirements_git.txt`, using `pip-tools` and `pip-compile`.

## How To Use

Commands should be run in the awx container from inside the `./requirements` directory of the awx repository.

### Upgrading or Adding Select Libraries

If you need to add or upgrade one targeted library, then modify `requirements.in`,
then run the script:

`./updater.sh run`

#### Upgrading Unpinned Dependency

If you require a new version of a dependency that does not have a pinned version
for a fix or feature, pin a minimum version in `requirements.in` and run `./updater.sh run`. For example,
replace the line `asgi-amqp` with `asgi-amqp>=1.1.4`, and consider leaving a
note.

Then next time that a general upgrade is performed, the minimum version specifiers
can be removed, because `*.txt` files are upgraded to latest.

### Upgrading Dependencies

You can upgrade (`pip-compile --upgrade`) the dependencies by running

`./updater.sh upgrade`.

## Licenses and Source Files

If any library has a change to its license with the upgrade, then the license for that library
inside of `licenses` needs to be updated.

For libraries that have source distribution requirements (LGPL as an example),
a tarball of the library is kept along with the license.
To download the PyPI tarball, you can run this command:

```
pip download <pypi library name> -d licenses/ --no-binary :all: --no-deps
```

Make sure to delete the old tarball if it is an upgrade.

## UPGRADE BLOCKERs

Anything pinned in `*.in` files involves additional manual work in
order to upgrade. Some information related to that work is outlined here.

### social-auth-app-django

django-social keeps a list of backends in memory that it gathers
based on the value of `settings.AUTHENTICATION_BACKENDS` *at import time*:
https://github.com/python-social-auth/social-app-django/blob/c1e2795b00b753d58a81fa6a0261d8dae1d9c73d/social_django/utils.py#L13

Our `settings.AUTHENTICATION_BACKENDS` can *change*
dynamically as settings are changed (i.e., if somebody
configures Github OAuth2 integration), so we need to
_overwrite_ this in-memory value at the top of every request so
that we have the latest version

### django-oauth-toolkit

Versions later than 1.4.1 throw an error about id_token_id, due to the
OpenID Connect work that was done in
https://github.com/jazzband/django-oauth-toolkit/pull/915.  This may
be fixable by creating a migration on our end?

### pip, setuptools and setuptools_scm

If modifying these libraries make sure testing with the offline build is performed to confirm they are functionally working.
Versions need to match the versions used in the pip bootstrapping step
in the top-level Makefile.

### cryptography

If modifying this library make sure testing with the offline build is performed to confirm it is functionally working.

### channels-redis

Due to an upstream bug (linked below), we see `RuntimeError: Event loop is closed` errors with newer versions of `channels-redis`.
Upstream is aware of the bug and it is likely to be fixed in the next release according to the issue linked below.
For now, we pin to the old version, 3.4.1

* https://github.com/django/channels_redis/issues/332
* https://github.com/ansible/awx/issues/13313

### hiredis

The hiredis 2.1.0 release doesn't provide source distribution on PyPI which prevents users to build that python package from the
sources.
Downgrading to 2.0.0 (which provides source distribution) until the channels-redis issue is fixed or a newer hiredis version is
available on PyPi with source distribution.

* https://github.com/redis/hiredis-py/issues/138

## Library Notes

### pexpect

Version 4.8 makes us a little bit nervous with changes to `searchwindowsize` https://github.com/pexpect/pexpect/pull/579/files
Pin to `pexpect==4.7.x` until we have more time to move to `4.8` and test.
