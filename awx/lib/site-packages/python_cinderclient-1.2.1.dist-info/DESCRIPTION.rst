Python bindings to the OpenStack Cinder API
===========================================

This is a client for the OpenStack Cinder API. There's a Python API (the
``cinderclient`` module), and a command-line script (``cinder``). Each
implements 100% of the OpenStack Cinder API.

See the `OpenStack CLI guide`_ for information on how to use the ``cinder``
command-line tool. You may also want to look at the
`OpenStack API documentation`_.

.. _OpenStack CLI Guide: http://docs.openstack.org/cli/quick-start/content/
.. _OpenStack API documentation: http://docs.openstack.org/api/

The project is hosted on `Launchpad`_, where bugs can be filed. The code is
hosted on `Github`_. Patches must be submitted using `Gerrit`_, *not* Github
pull requests.

.. _Github: https://github.com/openstack/python-cinderclient
.. _Launchpad: https://launchpad.net/python-cinderclient
.. _Gerrit: http://docs.openstack.org/infra/manual/developers.html#development-workflow

This code a fork of `Jacobian's python-cloudservers`__ If you need API support
for the Rackspace API solely or the BSD license, you should use that repository.
python-cinderclient is licensed under the Apache License like the rest of OpenStack.

__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Command-line API
----------------

Installing this package gets you a shell command, ``cinder``, that you
can use to interact with any Rackspace compatible API (including OpenStack).

You'll need to provide your OpenStack username and password. You can do this
with the ``--os-username``, ``--os-password`` and  ``--os-tenant-name``
params, but it's easier to just set them as environment variables::

    export OS_USERNAME=openstack
    export OS_PASSWORD=yadayada
    export OS_TENANT_NAME=myproject

You will also need to define the authentication url with ``--os-auth-url``
and the version of the API with ``--os-volume-api-version``.  Or set them as
environment variables as well::

    export OS_AUTH_URL=http://example.com:8774/v1.1/
    export OS_VOLUME_API_VERSION=1

If you are using Keystone, you need to set the OS_AUTH_URL to the keystone
endpoint::

    export OS_AUTH_URL=http://example.com:5000/v2.0/

Since Keystone can return multiple regions in the Service Catalog, you
can specify the one you want with ``--os-region-name`` (or
``export OS_REGION_NAME``). It defaults to the first in the list returned.

You'll find complete documentation on the shell by running
``cinder help``::

    usage: cinder [--debug] [--os-username <auth-user-name>]
                  [--os-password <auth-password>]
                  [--os-tenant-name <auth-tenant-name>] [--os-auth-url <auth-url>]
                  [--os-region-name <region-name>] [--service-type <service-type>]
                  [--service-name <service-name>]
                  [--volume-service-name <volume-service-name>]
                  [--endpoint-type <endpoint-type>]
                  [--os-volume-api-version <compute-api-ver>]
                  [--os-cacert <ca-certificate>] [--retries <retries>]
                  <subcommand> ...

    Command-line interface to the OpenStack Cinder API.

    Positional arguments:
      <subcommand>
        absolute-limits     Print a list of absolute limits for a user
        create              Add a new volume.
        credentials         Show user credentials returned from auth
        delete              Remove a volume.
        endpoints           Discover endpoints that get returned from the
                            authenticate services
        extra-specs-list    Print a list of current 'volume types and extra specs'
                            (Admin Only).
        list                List all the volumes.
        quota-class-show    List the quotas for a quota class.
        quota-class-update  Update the quotas for a quota class.
        quota-defaults      List the default quotas for a tenant.
        quota-show          List the quotas for a tenant.
        quota-update        Update the quotas for a tenant.
        rate-limits         Print a list of rate limits for a user
        rename              Rename a volume.
        show                Show details about a volume.
        snapshot-create     Add a new snapshot.
        snapshot-delete     Remove a snapshot.
        snapshot-list       List all the snapshots.
        snapshot-rename     Rename a snapshot.
        snapshot-show       Show details about a snapshot.
        type-create         Create a new volume type.
        type-delete         Delete a specific volume type
        type-key            Set or unset extra_spec for a volume type.
        type-list           Print a list of available 'volume types'.
        bash-completion     Prints all of the commands and options to stdout so
                            that the
        help                Display help about this program or one of its
                            subcommands.
        list-extensions     List all the os-api extensions that are available.

    Optional arguments:
      -d, --debug               Print debugging output
      --os-username <auth-user-name>
                            Defaults to env[OS_USERNAME].
      --os-password <auth-password>
                            Defaults to env[OS_PASSWORD].
      --os-tenant-name <auth-tenant-name>
                            Defaults to env[OS_TENANT_NAME].
      --os-auth-url <auth-url>
                            Defaults to env[OS_AUTH_URL].
      --os-region-name <region-name>
                            Defaults to env[OS_REGION_NAME].
      --service-type <service-type>
                            Defaults to compute for most actions
      --service-name <service-name>
                            Defaults to env[CINDER_SERVICE_NAME]
      --volume-service-name <volume-service-name>
                            Defaults to env[CINDER_VOLUME_SERVICE_NAME]
      --endpoint-type <endpoint-type>
                            Defaults to env[CINDER_ENDPOINT_TYPE] or publicURL.
      --os-volume-api-version <compute-api-ver>
                            Accepts 1,defaults to env[OS_VOLUME_API_VERSION].
      --os-cacert <ca-certificate>
                            Specify a CA bundle file to use in verifying a TLS
                            (https) server certificate. Defaults to env[OS_CACERT]
      --retries <retries>   Number of retries.

Python API
----------

There's also a complete Python API, but it has not yet been documented.

Quick-start using keystone::

    # use v2.0 auth with http://example.com:5000/v2.0/")
    >>> from cinderclient.v1 import client
    >>> nt = client.Client(USER, PASS, TENANT, AUTH_URL, service_type="volume")
    >>> nt.volumes.list()
    [...]

See release notes and more at `<http://docs.openstack.org/developer/python-cinderclient/>`_.

* License: Apache License, Version 2.0
* Documentation: http://docs.openstack.org/developer/python-cinderclient
* Source: http://git.openstack.org/cgit/openstack/python-cinderclient
* Bugs: http://bugs.launchpad.net/python-cinderclient



