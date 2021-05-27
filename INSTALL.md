Table of Contents
=================

   * [Installing AWX](#installing-awx)
      * [The AWX Operator](#the-awx-operator)
   * [Installing the AWX CLI](#installing-the-awx-cli)
      * [Building the CLI Documentation](#building-the-cli-documentation)


# Installing AWX

:warning: NOTE |
--- |
If you're installing an older release of AWX (prior to 18.0), these instructions have changed.  Take a look at your version specific instructions, e.g., for AWX 17.0.1, see: [https://github.com/ansible/awx/blob/17.0.1/INSTALL.md](https://github.com/ansible/awx/blob/17.0.1/INSTALL.md)
If you're attempting to migrate an older Docker-based AWX installation, see: [Migrating Data from Local Docker](https://github.com/ansible/awx/blob/devel/tools/docker-compose/docs/data_migration.md) |

## The AWX Operator

Starting in version 18.0, the [AWX Operator](https://github.com/ansible/awx-operator) is the preferred way to install AWX. Please refer to the [AWX Operator](https://github.com/ansible/awx-operator) documentation.

AWX can also alternatively be installed and [run in Docker](./tools/docker-compose/README.md), but this install path is only recommended for development/test-oriented deployments, and has no official published release.

# Installing the AWX CLI

`awx` is the official command-line client for AWX.  It:

* Uses naming and structure consistent with the AWX HTTP API
* Provides consistent output formats with optional machine-parsable formats
* To the extent possible, auto-detects API versions, available endpoints, and
  feature support across multiple versions of AWX.

Potential uses include:

* Configuring and launching jobs/playbooks
* Checking on the status and output of job runs
* Managing objects like organizations, users, teams, etc...

The preferred way to install the AWX CLI is through pip directly from PyPI:

    pip3 install awxkit
    awx --help

## Building the CLI Documentation

To build the docs, spin up a real AWX server, `pip3 install sphinx sphinxcontrib-autoprogram`, and run:

    ~ cd awxkit/awxkit/cli/docs
    ~ TOWER_HOST=https://awx.example.org TOWER_USERNAME=example TOWER_PASSWORD=secret make clean html
    ~ cd build/html/ && python -m http.server
    Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ..
