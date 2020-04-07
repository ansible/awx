.. _authentication:

Authentication
==============

Generating a Personal Access Token
----------------------------------

The preferred mechanism for authenticating with AWX and |RHAT| is by generating and storing an OAuth2.0 token.  Tokens can be scoped for read/write permissions, are easily revoked, and are more suited to third party tooling integration than session-based authentication.

|prog| provides a simple login command for generating a personal access token from your username and password.

.. code:: bash

    TOWER_HOST=https://awx.example.org \
        TOWER_USERNAME=alice \
        TOWER_PASSWORD=secret \
        awx login

As a convenience, the ``awx login -f human`` command prints a shell-formatted token
value:

.. code:: bash

    export TOWER_OAUTH_TOKEN=6E5SXhld7AMOhpRveZsLJQsfs9VS8U

By ingesting this token, you can run subsequent CLI commands without having to
specify your username and password each time:

.. code:: bash

    export TOWER_HOST=https://awx.example.org
    $(TOWER_USERNAME=alice TOWER_PASSWORD=secret awx login -f human)
    awx config

Working with OAuth2.0 Applications
----------------------------------

AWX and |RHAT| allow you to configure OAuth2.0 applications scoped to specific
organizations.  To generate an application token (instead of a personal access
token), specify the **Client ID** and **Client Secret** generated when the
application was created.

.. code:: bash

    TOWER_USERNAME=alice TOWER_PASSWORD=secret awx login \
        --conf.client_id <value> --conf.client_secret <value>


OAuth2.0 Token Scoping
----------------------

By default, tokens created with ``awx login`` are write-scoped.  To generate
a read-only token, specify ``--scope read``:

.. code:: bash

    TOWER_USERNAME=alice TOWER_PASSWORD=secret \
        awx login --conf.scope read

Session Authentication
----------------------
If you do not want or need to generate a long-lived token, |prog| allows you to
specify your username and password on every invocation:

.. code:: bash

    TOWER_USERNAME=alice TOWER_PASSWORD=secret awx jobs list
    awx --conf.username alice --conf.password secret jobs list
