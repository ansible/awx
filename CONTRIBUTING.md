
Ansible AWX
===========

Hi there! We're excited to have you as a contributor.

Have questions about this document or anything not covered here? Come chat with us on IRC (#ansible-awx on freenode) or the mailing list.

Table of contents
-----------------

* [Contributing Agreement](#dco)
* [Code of Conduct](#code-of-conduct)
* [Setting up the development environment](#setting-up-the-development-environment)
  * [Prerequisites](#prerequisites)
  * [Local Settings](#local-settings)
  * [Building the base image](#building-the-base-image)
  * [Building the user interface](#building-the-user-interface)
  * [Starting up the development environment](#starting-up-the-development-environment)
  * [Starting the development environment at the container shell](#starting-the-container-environment-at-the-container-shell)
  * [Using the development environment](#using-the-development-environment)
* [What should I work on?](#what-should-i-work-on)
* [Submitting Pull Requests](#submitting-pull-requests)
* [Reporting Issues](#reporting-issues)
  * [How issues are resolved](#how-issues-are-resolved)
  * [Ansible Issue Bot](#ansible-issue-bot)

DCO
===

All contributors must use "git commit --signoff" for any
commit to be merged, and agree that usage of --signoff constitutes
agreement with the terms of DCO 1.1.  Any contribution that does not
have such a signoff will not be merged.

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
1 Letterman Drive
Suite D4700
San Francisco, CA, 94129

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

Code of Conduct
===============

Setting up the development environment
======================================

The AWX development environment workflow and toolchain is based on Docker and the docker-compose tool to contain
the dependencies, services, and databases necessary to run everything. It will bind the local source tree into the container
making it possible to observe changes while developing.

Prerequisites
-------------
`docker` and `docker-compose` are required for starting the development services, on Linux you can generally find these in your
distro's packaging, but you may find that Docker themselves maintain a seperate repo that tracks more closely to the latest releases.
For macOS and Windows, we recommend Docker for Mac (https://www.docker.com/docker-mac) and Docker for Windows (https://www.docker.com/docker-windows) 
respectively. Docker for Mac/Windows automatically comes with `docker-compose`.

> Fedora

https://docs.docker.com/engine/installation/linux/docker-ce/fedora/

> Centos

https://docs.docker.com/engine/installation/linux/docker-ce/centos/

> Ubuntu

https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/

> Debian

https://docs.docker.com/engine/installation/linux/docker-ce/debian/

> Arch

https://wiki.archlinux.org/index.php/Docker

For `docker-compose` you may need/choose to install it seperately:

    pip install docker-compose


Local Settings
--------------

In development mode (i.e. when running from a source checkout), Ansible AWX
will import the file `awx/settings/local_settings.py` and combine it with defaults in `awx/settings/defaults.py`. This file
is required for starting the development environment and startup will fail if it's not provided

An example file that works for the `docker-compose` tool is provided. Make a copy of it and edit as needed (the defaults are usually fine):

    (host)$ cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py

Building the base image
-----------------------

The AWX base container image (found in `tools/docker-compose/Dockerfile`) contains basic OS dependencies and
symbolic links into the development environment that make running the services easy. You'll first need to build the image:

    (host)$ make docker-compose-build

The image will only need to be rebuilt if the requirements or OS dependencies change. A core concept about this image is that it relies
on having your local development environment mapped in.

Building the user interface
---------------------------

> AWX requires the 6.x LTS version of Node and 3.x LTS NPM

In order for the AWX user interface to load from the development environment it must be built:

    (host)$ make ui-devel
    
When developing features and fixes for the user interface you can find more detail here: [UI Developer README](awx/ui/README.md)

Starting up the development environment
----------------------------------------------

There are several ways of starting the development environment depending on your desired workflow. The easiest and most common way is with:

    (host)$ make docker-compose
    
This utilizes the image you built in the previous step and will automatically start all required services and dependent containers. You'll
be able to watch log messages and events as they come through.

The Makefile assumes that the image you built is tagged with your current branch. This allows you to pre-build images for different contexts
but you may want to use a particular branch's image (for instance if you are developing a PR from a branch based on the integration branch):

    (host)$ COMPOSE_TAG=devel make docker-compose

Starting the development environment at the container shell
-----------------------------------------------------------

Often times you'll want to start the development environment without immediately starting all services and instead be taken directly to a shell:

    (host)$ make docker-compose-test

From here you'll need to bootstrap the development environment before it will be usable for you. The `docker-compose` make target will
automatically do this:

    (container)$ /bootstrap_development.sh
    
From here you can start each service individually, or choose to start all service in a pre-configured tmux session:

    (container)# cd /awx_devel
    (container)# make server

Using the development environment
---------------------------------

With the development environment running there are a few optional steps to pre-populate the environment with data. If you are using the `docker-compose`
method above you'll first need a shell in the container:

    (host)$ docker exec -it tools_awx_1 bash

Create a superuser account:

    (container)# awx-manage createsuperuser
    
Preload AWX with demo data:

    (container)# awx-manage create_preload_data
    
This information will persist in the database running in the `tools_postgres_1` container, until it is removed. You may periodically need to recreate
this container and database if the database schema changes in an upstream commit.

You should now be able to visit and login to the AWX user interface at https://localhost:8043 or http://localhost:8013 if you have built the UI.
If not you can visit the API directly in your browser at: https://localhost:8043/api/ or http://localhost:8013/api/

When working on the source code for AWX the code will auto-reload for you when changes are made, with the exception of any background tasks that run in
celery.

Occasionally it may be necessary to purge any containers and images that may have collected:

    (host)$ make docker-clean
    
There are host of other shortcuts, tools, and container configurations in the Makefile designed for various purposes. Feel free to explore.
    
What should I work on?
======================

We list our specs in `/docs`. `/docs/current` are things that we are actively working on. `/docs/future` are ideas for future work and the direction we
want that work to take. Fixing bugs, translations, and updates to documentation are also appreciated.

Be aware that if you are working in a part of the codebase that is going through active development your changes may be rejected or you may be asked to
rebase them. A good idea before starting work is to have a discussion with us on IRC or the mailing list.

Submitting Pull Requests
========================

Fixes and Features for AWX will go through the Github PR interface. There are a few things that can be done to help the visibility of your change
and increase the likelihood that it will be accepted

> Add UI detail to these

* No issues when running linters/code checkers
  * Python: flake8: `(container)/awx_devel$ make flake8`
  * Javascript: JsHint: `(container)/awx_devel$ make jshint`
* No issues from unit tests
  * Python: py.test: `(container)/awx_devel$ make test`
  * JavaScript: Jasmine: `(container)/awx_devel$ make ui-test-ci`
* Write tests for new functionality, update/add tests for bug fixes
* Make the smallest change possible
* Write good commit messages: https://chris.beams.io/posts/git-commit/

It's generally a good idea to discuss features with us first by engaging us in IRC or on the mailing list, especially if you are unsure if it's a good
fit.

We like to keep our commit history clean and will require resubmission of pull requests that contain merge commits. Use `git pull --rebase` rather than
`git pull` and `git rebase` rather than `git merge`.

Sometimes it might take us a while to fully review your PR. We try to keep the `devel` branch in pretty good working order so we review requests carefuly.
Please be patient.

All submitted PRs will have the linter and unit tests run against them and the status reported in the PR.

Reporting Issues
================

Use the Github issue tracker for filing bugs. In order to save time and help us respond to issues quickly, make sure to fill out as much of the issue template
as possible. Version information and an accurate reproducing scenario are critical to helping us identify the problem.

When reporting issues for the UI we also appreciate having screenshots and any error messages from the web browser's console. It's not unsual for browser extensions
and plugins to cause problems. Reporting those will also help speed up analyzing and resolving UI bugs.

For the API and backend services, please capture all of the logs that you can from the time the problem was occuring.

Don't use the issue tracker to get help on how to do something - please use the mailing list and IRC for that.

How issues are resolved
-----------------------

We triage our issues into high, medium, and low and will tag them with the relevant component (api, ui, installer, etc). We will typically focus on high priority
issues. There aren't hard and fast rules for determining the severity of an issue, but generally high priority issues have an increased likelihood of breaking
existing functionality and/or negatively impacting a large number of users.

If your issue isn't considered `high` priority then please be patient as it may take some time to get to your report.

Before opening a new issue, please use the issue search feature to see if it's already been reported. If you have any extra detail to provide then please comment.
Rather than posting a "me too" comment you might consider giving it a "thumbs up" on github.

Ansible Issue Bot
-----------------
> Fill in
