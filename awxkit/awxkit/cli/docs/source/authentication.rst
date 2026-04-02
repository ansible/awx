.. _authentication:

Authentication
==============

OAuth2 Token Authentication
---------------------------

If your AWX account uses social authentication (e.g., GitHub, SAML, OIDC) and you do not have a local password, you can authenticate using an OAuth2 personal access token.

Create a token in the AWX UI (User → Tokens → Add), then provide it using one of the following methods:

.. code:: bash

    CONTROLLER_OAUTH_TOKEN=my_token awx jobs list
    awx --conf.token my_token jobs list

Token authentication takes precedence over username/password when both are provided.

Username and Password Authentication
------------------------------------

To authenticate with a username and password:

.. code:: bash

    CONTROLLER_USERNAME=alice CONTROLLER_PASSWORD=secret awx jobs list
    awx --conf.username alice --conf.password secret jobs list
