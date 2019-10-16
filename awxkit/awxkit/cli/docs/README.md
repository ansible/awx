AWX Command Line Interface
==========================

`awx` is the official command-line client for AWX.  It:

* Uses naming and structure consistent with the AWX HTTP API
* Provides consistent output formats with optional machine-parsable formats
* To the extent possible, auto-detects API versions, available endpoints, and
  feature support across multiple versions of AWX.

Potential uses include:

* Configuring and launching jobs/playbooks
* Checking on the status and output of job runs
* Managing objects like organizations, users, teams, etc...

Installation
------------

The preferred way to install the AWX CLI is through pip directly from GitHub:

    pip install "https://github.com/ansible/awx/archive/$VERSION.tar.gz#egg=awxkit&subdirectory=awxkit"
    awx --help

...where ``$VERSION`` is the version of AWX you're running.  To see a list of all available releases, visit: https://github.com/ansible/awx/releases

Building the Documentation
--------------------------
To build the docs, spin up a real AWX server, `pip install sphinx sphinxcontrib-autoprogram`, and run:

    ~ TOWER_HOST=https://awx.example.org TOWER_USERNAME=example TOWER_PASSWORD=secret make clean html
    ~ cd build/html/ && python -m http.server
    Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ..
