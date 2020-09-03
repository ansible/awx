# AWX

Hi there! We're excited to have you as a contributor.

Have questions about this document or anything not covered here? Come chat with us at `#ansible-awx` on irc.freenode.net, or submit your question to the [mailing list](https://groups.google.com/forum/#!forum/awx-project).

## Table of contents

* [Things to know prior to submitting code](#things-to-know-prior-to-submitting-code)
* [Setting up your development environment](#setting-up-your-development-environment)
  * [Prerequisites](#prerequisites)
    * [Docker](#docker)
    * [Docker compose](#docker-compose)
    * [Node and npm](#node-and-npm)
  * [Build the environment](#build-the-environment)
    * [Fork and clone the AWX repo](#fork-and-clone-the-awx-repo)
    * [Create local settings](#create-local-settings)
    * [Build the base image](#build-the-base-image)
    * [Build the user interface](#build-the-user-interface)
  * [Running the environment](#running-the-environment)
    * [Start the containers](#start-the-containers)
    * [Start from the container shell](#start-from-the-container-shell)
  * [Post Build Steps](#post-build-steps)
    * [Start a shell](#start-a-shell)
    * [Create a superuser](#create-a-superuser)
    * [Load the data](#load-the-data)
    * [Building API Documentation](#build-api-documentation)
  * [Accessing the AWX web interface](#accessing-the-awx-web-interface)
  * [Purging containers and images](#purging-containers-and-images)
* [What should I work on?](#what-should-i-work-on)
* [Submitting Pull Requests](#submitting-pull-requests)
* [Reporting Issues](#reporting-issues)

## Things to know prior to submitting code

- All code submissions are done through pull requests against the `devel` branch.
- You must use `git commit --signoff` for any commit to be merged, and agree that usage of --signoff constitutes agreement with the terms of [DCO 1.1](./DCO_1_1.md).
- Take care to make sure no merge commits are in the submission, and use `git rebase` vs `git merge` for this reason.
  - If collaborating with someone else on the same branch, consider using `--force-with-lease` instead of `--force`. This will prevent you from accidentally overwriting commits pushed by someone else. For more information, see https://git-scm.com/docs/git-push#git-push---force-with-leaseltrefnamegt
- If submitting a large code change, it's a good idea to join the `#ansible-awx` channel on irc.freenode.net, and talk about what you would like to do or add first. This not only helps everyone know what's going on, it also helps save time and effort, if the community decides some changes are needed.
- We ask all of our community members and contributors to adhere to the [Ansible code of conduct](http://docs.ansible.com/ansible/latest/community/code_of_conduct.html). If you have questions, or need assistance, please reach out to our community team at [codeofconduct@ansible.com](mailto:codeofconduct@ansible.com)

## Setting up your development environment

The AWX development environment workflow and toolchain is based on Docker, and the docker-compose tool, to provide dependencies, services, and databases necessary to run all of the components. It also binds the local source tree into the development container, making it possible to observe and test changes in real time.

### Prerequisites

#### Docker

Prior to starting the development services, you'll need `docker` and `docker-compose`. On Linux, you can generally find these in your distro's packaging, but you may find that Docker themselves maintain a separate repo that tracks more closely to the latest releases.

For macOS and Windows, we recommend [Docker for Mac](https://www.docker.com/docker-mac) and [Docker for Windows](https://www.docker.com/docker-windows)
respectively.

For Linux platforms, refer to the following from Docker:

**Fedora**

> https://docs.docker.com/engine/installation/linux/docker-ce/fedora/

**CentOS**

> https://docs.docker.com/engine/installation/linux/docker-ce/centos/

**Ubuntu**

> https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/

**Debian**

> https://docs.docker.com/engine/installation/linux/docker-ce/debian/

**Arch**

> https://wiki.archlinux.org/index.php/Docker

#### Docker compose

If you're not using Docker for Mac, or Docker for Windows, you may need, or choose to, install the Docker compose Python module separately, in which case you'll need to run the following:

```bash
(host)$ pip3 install docker-compose
```

#### Frontend Development

See [the ui development documentation](awx/ui/README.md).


### Build the environment

#### Fork and clone the AWX repo

If you have not done so already, you'll need to fork the AWX repo on GitHub. For more on how to do this, see [Fork a Repo](https://help.github.com/articles/fork-a-repo/).

#### Create local settings

AWX will import the file `awx/settings/local_settings.py` and combine it with defaults in `awx/settings/defaults.py`. This file is required for starting the development environment and startup will fail if it's not provided.

An example is provided. Make a copy of it, and edit as needed (the defaults are usually fine):

```bash
(host)$ cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py
```

#### Build the base image

The AWX base container image (defined in `tools/docker-compose/Dockerfile`) contains basic OS dependencies and symbolic links into the development environment that make running the services easy.

Run the following to build the image:

```bash
(host)$ make docker-compose-build
```

**NOTE**

> The image will need to be rebuilt, if the Python requirements or OS dependencies change.

Once the build completes, you will have a `ansible/awx_devel` image in your local image cache. Use the `docker images` command to view it, as follows:

```bash
(host)$ docker images

REPOSITORY                                   TAG                 IMAGE ID            CREATED             SIZE
ansible/awx_devel                            latest              ba9ec3e8df74        26 minutes ago      1.42GB
```

#### Build the user interface

Run the following to build the AWX UI:

```bash
(host) $ make ui-devel
```
See [the ui development documentation](awx/ui/README.md) for more information on using the frontend development, build, and test tooling.

### Running the environment

#### Start the containers

Start the development containers by running the following:

```bash
(host)$ make docker-compose
```

The above utilizes the image built in the previous step, and will automatically start all required services and dependent containers. Once the containers launch, your session will be attached to the *awx* container, and you'll be able to watch log messages and events in real time. You will see messages from Django and the front end build process.

If you start a second terminal session, you can take a look at the running containers using the `docker ps` command. For example:

```bash
# List running containers
(host)$ docker ps

$ docker ps
CONTAINER ID        IMAGE                                              COMMAND                  CREATED             STATUS              PORTS                                                                                                                                                              NAMES
44251b476f98        gcr.io/ansible-tower-engineering/awx_devel:devel   "/entrypoint.sh /bin…"   27 seconds ago      Up 23 seconds       0.0.0.0:6899->6899/tcp, 0.0.0.0:7899-7999->7899-7999/tcp, 0.0.0.0:8013->8013/tcp, 0.0.0.0:8043->8043/tcp, 0.0.0.0:8080->8080/tcp, 22/tcp, 0.0.0.0:8888->8888/tcp   tools_awx_run_9e820694d57e
40de380e3c2e        redis:latest                                       "docker-entrypoint.s…"   28 seconds ago      Up 26 seconds
b66a506d3007        postgres:10                                        "docker-entrypoint.s…"   28 seconds ago      Up 26 seconds       0.0.0.0:5432->5432/tcp                                                                                                                                             tools_postgres_1
```
**NOTE**

> The Makefile assumes that the image you built is tagged with your current branch. This allows you to build images for different contexts or branches. When starting the containers, you can choose a specific branch by setting `COMPOSE_TAG=<branch name>` in your environment.

> For example, you might be working in a feature branch, but you want to run the containers using the `devel` image you built previously. To do that, start the containers using the following command: `$ COMPOSE_TAG=devel make docker-compose`

##### Wait for migrations to complete

The first time you start the environment, database migrations need to run in order to build the PostgreSQL database. It will take few moments, but eventually you will see output in your terminal session that looks like the following:

```bash
awx_1        | Operations to perform:
awx_1        |   Synchronize unmigrated apps: solo, api, staticfiles, debug_toolbar, messages, channels, django_extensions, ui, rest_framework, polymorphic
awx_1        |   Apply all migrations: sso, taggit, sessions, sites, kombu_transport_django, social_auth, contenttypes, auth, conf, main
awx_1        | Synchronizing apps without migrations:
awx_1        |   Creating tables...
awx_1        |     Running deferred SQL...
awx_1        |   Installing custom SQL...
awx_1        | Running migrations:
awx_1        |   Rendering model states... DONE
awx_1        |   Applying contenttypes.0001_initial... OK
awx_1        |   Applying contenttypes.0002_remove_content_type_name... OK
awx_1        |   Applying auth.0001_initial... OK
awx_1        |   Applying auth.0002_alter_permission_name_max_length... OK
awx_1        |   Applying auth.0003_alter_user_email_max_length... OK
awx_1        |   Applying auth.0004_alter_user_username_opts... OK
awx_1        |   Applying auth.0005_alter_user_last_login_null... OK
awx_1        |   Applying auth.0006_require_contenttypes_0002... OK
awx_1        |   Applying taggit.0001_initial... OK
awx_1        |   Applying taggit.0002_auto_20150616_2121... OK
awx_1        |   Applying main.0001_initial... OK
awx_1        |   Applying main.0002_squashed_v300_release... OK
awx_1        |   Applying main.0003_squashed_v300_v303_updates... OK
awx_1        |   Applying main.0004_squashed_v310_release... OK
awx_1        |   Applying conf.0001_initial... OK
awx_1        |   Applying conf.0002_v310_copy_tower_settings... OK
...
```

Once migrations are completed, you can begin using AWX.

#### Start from the container shell

Often times you'll want to start the development environment without immediately starting all of the services in the *awx* container, and instead be taken directly to a shell. You can do this with the following:

```bash
(host)$ make docker-compose-test
```

Using `docker exec`, this will create a session in the running *awx* container, and place you at a command prompt, where you can run shell commands inside the container.

If you want to start and use the development environment, you'll first need to bootstrap it by running the following command:

```bash
(container)# /usr/bin/bootstrap_development.sh
```

The above will do all the setup tasks, including running database migrations, so it may take a couple minutes. Once it's done it
will drop you back to the shell.

In order to launch all developer services:

```bash
(container)# /usr/bin/launch_awx.sh
```

`launch_awx.sh` also calls `bootstrap_development.sh` so if all you are doing is launching the supervisor to start all services, you don't
need to call `bootstrap_development.sh` first.



### Post Build Steps

Before you can log in and use the system, you will need to create an admin user. Optionally, you may also want to load some demo data.

##### Start a shell

To create the admin user, and load demo data, you first need to start a shell session on the *awx* container. In a new terminal session, use the `docker exec` command as follows to start the shell session:

```bash
(host)$ docker exec -it tools_awx_1 bash
```
This creates a session in the *awx* containers, just as if you were using `ssh`, and allows you execute commands within the running container.

##### Create an admin user

Before you can log into AWX, you need to create an admin user. With this user you will be able to create more users, and begin configuring the server. From within the container shell, run the following command:

```bash
(container)# awx-manage createsuperuser
```
You will be prompted for a username, an email address, and a password, and you will be asked to confirm the password. The email address is not important, so just enter something that looks like an email address. Remember the username and password, as you will use them to log into the web interface for the first time.

##### Load demo data

You can optionally load some demo data. This will create a demo project, inventory, and job template. From within the container shell, run the following to load the data:

```bash
(container)# awx-manage create_preload_data
```

**NOTE**

> This information will persist in the database running in the `tools_postgres_1` container, until the container is removed. You may periodically need to recreate
this container, and thus the database, if the database schema changes in an upstream commit.

##### Building API Documentation

AWX includes support for building [Swagger/OpenAPI
documentation](https://swagger.io).  To build the documentation locally, run:

```bash
(container)/awx_devel$ make swagger
```

This will write a file named `swagger.json` that contains the API specification
in OpenAPI format.  A variety of online tools are available for translating
this data into more consumable formats (such as HTML). http://editor.swagger.io
is an example of one such service.

### Accessing the AWX web interface

You can now log into the AWX web interface at [https://localhost:8043](https://localhost:8043), and access the API directly at [https://localhost:8043/api/](https://localhost:8043/api/).

To log in use the admin user and password you created above in [Create an admin user](#create-an-admin-user).

### Purging containers and images

When necessary, remove any AWX containers and images by running the following:

```bash
(host)$ make docker-clean
```

## What should I work on?

For feature work, take a look at the current [Enhancements](https://github.com/ansible/awx/issues?q=is%3Aissue+is%3Aopen+label%3Atype%3Aenhancement).

If it has someone assigned to it then that person is the person responsible for working the enhancement. If you feel like you could contribute then reach out to that person.

Fixing bugs, adding translations, and updating the documentation are always appreciated, so reviewing the backlog of issues is always a good place to start. For extra information on debugging tools, see [Debugging](https://github.com/ansible/awx/blob/devel/docs/debugging.md).

**NOTE**

> If you work in a part of the codebase that is going through active development, your changes may be rejected, or you may be asked to `rebase`. A good idea before starting work is to have a discussion with us in the `#ansible-awx` channel on irc.freenode.net, or on the [mailing list](https://groups.google.com/forum/#!forum/awx-project).

**NOTE**

> If you're planning to develop features or fixes for the UI, please review the [UI Developer doc](./awx/ui/README.md).

## Submitting Pull Requests

Fixes and Features for AWX will go through the Github pull request process. Submit your pull request (PR) against the `devel` branch.

Here are a few things you can do to help the visibility of your change, and increase the likelihood that it will be accepted:

* No issues when running linters/code checkers
  * Python: flake8: `(container)/awx_devel$ make flake8`
  * Javascript: JsHint: `(container)/awx_devel$ make jshint`
* No issues from unit tests
  * Python: py.test: `(container)/awx_devel$ make test`
  * JavaScript: Jasmine: `(container)/awx_devel$ make ui-test-ci`
* Write tests for new functionality, update/add tests for bug fixes
* Make the smallest change possible
* Write good commit messages. See [How to write a Git commit message](https://chris.beams.io/posts/git-commit/).

It's generally a good idea to discuss features with us first by engaging us in the `#ansible-awx` channel on irc.freenode.net, or on the [mailing list](https://groups.google.com/forum/#!forum/awx-project).

We like to keep our commit history clean, and will require resubmission of pull requests that contain merge commits. Use `git pull --rebase`, rather than
`git pull`, and `git rebase`, rather than `git merge`.

Sometimes it might take us a while to fully review your PR. We try to keep the `devel` branch in good working order, and so we review requests carefully. Please be patient.

All submitted PRs will have the linter and unit tests run against them via Zuul, and the status reported in the PR.

## PR Checks ran by Zuul
Zuul jobs for awx are defined in the [zuul-jobs](https://github.com/ansible/zuul-jobs) repo.

Zuul runs the following checks that must pass:
1) `tox-awx-api-lint`
2) `tox-awx-ui-lint`
3) `tox-awx-api`
4) `tox-awx-ui`
5) `tox-awx-swagger`

Zuul runs the following checks that are non-voting (can not pass but serve to inform PR reviewers):
1) `tox-awx-detect-schema-change`
    This check generates the schema and diffs it against a reference copy of the `devel` version of the schema.
    Reviewers should inspect the `job-output.txt.gz` related to the check if their is a failure (grep for `diff -u -b` to find beginning of diff).
    If the schema change is expected and makes sense in relation to the changes made by the PR, then you are good to go!
    If not, the schema changes should be fixed, but this decision must be enforced by reviewers.

## Reporting Issues

We welcome your feedback, and encourage you to file an issue when you run into a problem. But before opening a new issues, we ask that you please view our [Issues guide](./ISSUES.md).
