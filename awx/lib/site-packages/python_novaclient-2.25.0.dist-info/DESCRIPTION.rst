Python bindings to the OpenStack Nova API
==================================================

This is a client for the OpenStack Nova API. There's a Python API (the
``novaclient`` module), and a command-line script (``nova``). Each
implements 100% of the OpenStack Nova API.

See the `OpenStack CLI guide`_ for information on how to use the ``nova``
command-line tool. You may also want to look at the
`OpenStack API documentation`_.

.. _OpenStack CLI Guide: http://docs.openstack.org/cli/quick-start/content/
.. _OpenStack API documentation: http://docs.openstack.org/api/

The project is hosted on `Launchpad`_, where bugs can be filed. The code is
hosted on `Github`_. Patches must be submitted using `Gerrit`_, *not* Github
pull requests.

.. _Github: https://github.com/openstack/python-novaclient
.. _Launchpad: https://launchpad.net/python-novaclient
.. _Gerrit: http://docs.openstack.org/infra/manual/developers.html#development-workflow

python-novaclient is licensed under the Apache License like the rest of
OpenStack.


.. contents:: Contents:
   :local:

Command-line API
----------------

Installing this package gets you a shell command, ``nova``, that you
can use to interact with any OpenStack cloud.

You'll need to provide your OpenStack username and password. You can do this
with the ``--os-username``, ``--os-password`` and  ``--os-tenant-name``
params, but it's easier to just set them as environment variables::

    export OS_USERNAME=openstack
    export OS_PASSWORD=yadayada
    export OS_TENANT_NAME=myproject

You will also need to define the authentication url with ``--os-auth-url``
and the version of the API with ``--os-compute-api-version``.  Or set them as
an environment variables as well::

    export OS_AUTH_URL=http://example.com:8774/v1.1/
    export OS_COMPUTE_API_VERSION=2

If you are using Keystone, you need to set the OS_AUTH_URL to the keystone
endpoint::

    export OS_AUTH_URL=http://example.com:5000/v2.0/

Since Keystone can return multiple regions in the Service Catalog, you
can specify the one you want with ``--os-region-name`` (or
``export OS_REGION_NAME``). It defaults to the first in the list returned.

You'll find complete documentation on the shell by running
``nova help``

Python API
----------

There's also a complete Python API, but it has not yet been documented.


To use with nova, with keystone as the authentication system::

    # use v2.0 auth with http://example.com:5000/v2.0/")
    >>> from novaclient.v2 import client
    >>> nt = client.Client(USER, PASS, TENANT, AUTH_URL, service_type="compute")
    >>> nt.flavors.list()
    [...]
    >>> nt.servers.list()
    [...]
    >>> nt.keypairs.list()
    [...]


* License: Apache License, Version 2.0
* Documentation: http://docs.openstack.org/developer/python-novaclient
* Source: http://git.openstack.org/cgit/openstack/python-novaclient
* Bugs: http://bugs.launchpad.net/python-novaclient



