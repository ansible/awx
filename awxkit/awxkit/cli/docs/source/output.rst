.. _formatting:


Output Formatting
=================

By default, awx prints valid JSON for successful commands.  The ``-f`` (or
``--conf.format``) global flag can be used to specify alternative output
formats.

YAML Formatting
---------------

To print results in YAML, specify ``-f yaml``:

.. code:: bash

    awx jobs list -f yaml

Human-Readable (Tabular) Formatting
-----------------------------------

|prog| provides *optional* support for printing results in a human-readable
tabular format, but it requires an additional Python software dependency,
``tabulate``.

To use ``-f human``, you must install the optional dependency via ``pip install tabulate``.

.. code:: bash

    awx jobs list -f human
    awx jobs list -f human --filter name,created,status


Custom Formatting with jq
-------------------------

|prog| provides *optional* support for filtering results using the ``jq`` JSON
processor, but it requires an additional Python software dependency,
``jq``.

To use ``-f jq``, you must install the optional dependency via ``pip
install jq``.  Note that some platforms may require additional programs to
build ``jq`` from source (like ``libtool``).  See https://pypi.org/project/jq/ for instructions.

.. code:: bash

    awx jobs list \
        -f jq --filter '.results[] | .name + " is " + .status'

For details on ``jq`` filtering usage, see the ``jq`` manual at https://stedolan.github.io/jq/


Colorized Output
----------------

By default, |prog| prints colorized output using ANSI color codes.  To disable
this functionality, specify ``--conf.color f`` or set the environment variable
``TOWER_COLOR=f``.
