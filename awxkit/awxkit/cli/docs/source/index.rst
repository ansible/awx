.. AWX CLI documentation master file, created by
   sphinx-quickstart on Mon Jul 22 11:39:10 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

AWX Command Line Interface
==========================

|prog| is the official command-line client for AWX and |RHAT|.  It:

* Uses naming and structure consistent with the AWX HTTP API
* Provides consistent output formats with optional machine-parsable formats
* To the extent possible, auto-detects API versions, available endpoints, and
  feature support across multiple versions of AWX and |RHAT|.

Potential uses include:

* Configuring and launching jobs/playbooks
* Checking on the status and output of job runs
* Managing objects like organizations, users, teams, etc...

.. toctree::
   :maxdepth: 3

   usage
   authentication
   output
   examples
   reference

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
