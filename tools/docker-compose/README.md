# Docker Compose for Development

## Overview

Here are the main make targets:

* `docker-compose-build` - used for building the development image, which is used by the `docker-compose` target
* `docker-compose` - make target for development, passes awx_devel image and tag

Notable files:
* `tools/docker-compose/inventory` file - used to configure the local AWX development deploymen
* `migrate.yml` - playbook for migrating data from Local Docker to the Development Environment  

### Prerequisites

- [Docker](https://docs.docker.com/engine/installation/) on the host where AWX will be deployed. After installing Docker, the Docker service must be started (depending on your OS, you may have to add the local user that uses Docker to the ``docker`` group, refer to the documentation for details)
- [docker-compose](https://pypi.org/project/docker-compose/) Python module.
    + This also installs the `docker` Python module, which is incompatible with [`docker-py`](https://pypi.org/project/docker-py/). If you have previously installed `docker-py`, please uninstall it.
- [Docker Compose](https://docs.docker.com/compose/install/).
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) will need to be installed as we use it to template files needed for the docker-compose.

## Configuration

In the  [`inventory` file](../inventory), set your `pg_password`, `broadcast_websocket_secret`, `secret_key`, and any other settings you need for your deployment.  

AWX requires access to a PostgreSQL database, and by default, one will be created and deployed in a container, and data will be persisted to a docker volume. When the container is stopped, the database files will still exist in the docker volume. An external database can be used by setting the `pg_host`, `pg_hostname`, and `pg_username`.  

> If you are coming from a Local Docker installation of AWX, consider migrating your data first, see the [data migration section](#migrating-data-from-local-docker) below.  


## Starting the Development Environment

### Build the image

The AWX base container image (defined in the Dockerfile templated from [Dockerfile.j2](./../ansible/roles/dockerfile/templates/Dockerfile.j2)) contains basic OS dependencies and symbolic links into the development environment that make running the services easy.  

Run the following to build the image:

```bash
$ make docker-compose-build
```

> The image will need to be rebuilt if there are any changes to Dockerfile.j2 or any of the files used by the templated Dockerfile.  

Once the build completes, you will have a `ansible/awx_devel` image in your local image cache. Use the `docker images` command to view it, as follows:

```bash
(host)$ docker images

REPOSITORY                                   TAG                 IMAGE ID            CREATED             SIZE
ansible/awx_devel                            latest              ba9ec3e8df74        26 minutes ago      1.42GB
```

> By default, this image will be tagged with your branch name.  You can specify a custom tag by setting an environment variable, for example: `DEVEL_IMAGE_NAME=quay.io/your_user/awx_devel:17.0.1`

### Run AWX

##### Start the containers
Run the awx, postgres and redis containers. This utilizes the image built in the previous step, and will automatically start all required services and dependent containers. Once the containers launch, your session will be attached to the awx container, and you'll be able to watch log messages and events in real time. You will see messages from Django and the front end build process.

```bash
$ make docker-compose
```

> The make target assumes that the image you built is tagged with your current branch. This allows you to build images for different contexts or branches. When starting the containers, you can choose a specific branch by setting `COMPOSE_TAG=<branch name> `in your environment. For example, you might be working in a feature branch, but you want to run the containers using the devel image you built previously. To do that, start the containers using the following command: `$ COMPOSE_TAG=devel make docker-compose`

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
...
```

##### Clean and Build UI
```bash
$ docker exec tools_awx_1 make clean-ui ui-devel
```

See [the ui development documentation](../../awx/ui_next/README.md) for more information on using the frontend development, build, and test tooling.

Once migrations are completed and the UI is built, you can begin using AWX.  The UI can be reached in your browser at `https://localhost:8043/#/home`, and the API can be found at `https://localhost:8043/api/v2`.

##### Create an admin user

Before you can log into AWX, you need to create an admin user. With this user you will be able to create more users, and begin configuring the server. From within the container shell, run the following command:
```bash
$ docker exec -ti tools_awx_1 awx-manage createsuperuser
```

> Remember the username and password, as you will use them to log into the web interface for the first time.

##### Load Demo Data
Optionally, you may also want to load some demo data. This will create a demo project, inventory, and job template.

```bash
$ docker exec tools_awx_1 awx-manage create_preload_data
```

> This information will persist in the database running in the `tools_postgres_1` container, until the container is removed. You may periodically need to recreate
this container, and thus the database, if the database schema changes in an upstream commit.


## Migrating Data from Local Docker

If you are migrating data from a Local Docker installation (17.0.1 and prior), you can 
migrate your data to the development environment via the migrate.yml playbook using the steps described [here](./docs/data_migration.md).   

## Upgrading the Development Environment

Upgrading AWX involves checking out the new source code and re-running the make target. Download a newer release from [https://github.com/ansible/awx/releases](https://github.com/ansible/awx/releases) and re-populate the inventory file with your customized variables.

After updating the inventory file with any custom values, run the make target from the root of your AWX clone.  

```bash
$ make docker-compose
```

## Extras
* [Start a shell](#start-a-shell)
* [Start AWX from the container shell](#start-awx-from-the-container-shell)
* [Using Logstash](./docs/logstash.md)

### Start a Shell

To run `awx-manage` commands and modify things inside the container, you will want to start a shell session on the *awx* container. In a new terminal session, use the `docker exec` command to start the shell session:

```bash
(host)$ docker exec -it tools_awx_1 bash
```

This creates a session in the *awx* containers, just as if you were using `ssh`, and allows you execute commands within the running container.

### Start AWX from the container shell

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

### Start a cluster

Certain features or bugs are only applicable when running a cluster of AWX nodes. To bring up a 3 node cluster development environment simply run the below command.

```bash
(host)$ CLUSTER_NODE_COUNT=3 make docker-compose
```

`CLUSTER_NODE_COUNT` is configurable and defaults to 1, effectively a non-clustered AWX.

Note that you may see multiple messages of the form `2021-03-04 20:11:47,666 WARNING  [-] awx.main.wsbroadcast Connection from awx_2 to awx_5 failed: 'Cannot connect to host awx_5:8013 ssl:False [Name or service not known]'.`. This can happen when you bring up a cluster of many nodes, say 10, then you bring up a cluster of less nodes, say 3. In this example, there will be 7 `Instance` records in the database that represent AWX instances. The AWX development environment mimics the VM deployment (vs. kubernetes) and expects the missing nodes to be brought back to healthy by the admin. The warning message you are seeing is all of the AWX nodes trying to connect the websocket backplane. You can manually delete the `Instance` records from the database i.e. `Instance.objects.get(hostname='awx_9').delete()` to stop the warnings.
