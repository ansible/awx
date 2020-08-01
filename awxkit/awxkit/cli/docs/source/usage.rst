Basic Usage
===========

Installation
------------

.. include:: install.rst


Synopsis
--------

|prog| commands follow a simple format:

.. code:: bash

    awx [<global-options>] <resource> <action> [<arguments>]
    awx --help

The ``resource`` is a type of object within AWX (a noun), such as ``users`` or ``organizations``.

The ``action`` is the thing you want to do (a verb). Resources generally have a base set of actions (``get``, ``list``, ``create``, ``modify``, and ``delete``), and have options corresponding to fields on the object in AWX.  Some resources have special actions, like ``job_templates launch``.


Getting Started
---------------

Using |prog| requires some initial configuration.  Here is a simple example for interacting with an AWX or |RHAT| server:

.. code:: bash

    awx --conf.host https://awx.example.org \
        --conf.username joe --conf.password secret \
        --conf.insecure \
        users list

There are multiple ways to configure and authenticate with an AWX or |RHAT| server.  For more details, see :ref:`authentication`.

By default, |prog| prints valid JSON for successful commands.  Certain commands (such as those for printing job stdout) print raw text and do not allow for custom formatting.  For details on customizing |prog|'s output format, see :ref:`formatting`.


Resources and Actions
---------------------

To get a list of available resources:

.. code:: bash

    awx --conf.host https://awx.example.org --help

To get a description of a specific resource, and list its available actions (and their arguments):

.. code:: bash

    awx --conf.host https://awx.example.org users --help
    awx --conf.host https://awx.example.org users create --help


.. note:: The list of resources and actions may vary based on context.  For
    example, certain resources may not be available based on role-based access
    control (e.g., if you do not have permission to launch certain Job Templates,
    `launch` may not show up as an action for certain `job_templates` objects.


Global Options
--------------
|prog| accepts global options that control overall behavior.  In addition to CLI flags, most global options have a corresponding environment variable that may be used to set the value.  If both are provided, the command line option takes priority.

A few of the most important ones are:

``-h, --help``
    Prints usage information for the |prog| tool

``-v, --verbose``
    prints debug-level logs, including HTTP(s) requests made

``-f, --conf.format``
    used to specify a custom output format (the default is json)

``--conf.host, TOWER_HOST``
    the full URL of the AWX/|RHAT| host (i.e., https://my.awx.example.org)

``-k, --conf.insecure, TOWER_VERIFY_SSL``
    allows insecure server connections when using SSL

``--conf.username, TOWER_USERNAME``
    the AWX username to use for authentication

``--conf.password, TOWER_PASSWORD``
    the AWX password to use for authentication

``--conf.token, TOWER_OAUTH_TOKEN``
    an OAuth2.0 token to use for authentication
