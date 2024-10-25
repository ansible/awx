.. _authentication:

Authentication
==============

The only way to authenticate AWX is with username and password by specifying them on every invocation as shown in the following example:

.. code:: bash

    CONTROLLER_USERNAME=alice CONTROLLER_PASSWORD=secret awx jobs list
    awx --conf.username alice --conf.password secret jobs list
