.. _authentication:

Authentication
==============

To authenticate to AWX, include your username and password in each command invocation as shown in the following examples:

.. code:: bash

    CONTROLLER_USERNAME=alice CONTROLLER_PASSWORD=secret awx jobs list
    awx --conf.username alice --conf.password secret jobs list
