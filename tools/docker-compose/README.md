# Docker Compose for Development

## Getting started

### Clone the repo

If you have not already done so, you will need to clone, or create a local copy, of the [AWX repo](https://github.com/ansible/awx). We generally recommend that you view the releases page:

https://github.com/ansible/awx/releases/latest

...and clone the latest stable tag, e.g.,

`git clone -b x.y.z https://github.com/ansible/awx.git`

Please note that deploying from `HEAD` (or the latest commit) is **not** stable, and that if you want to do this, you should proceed at your own risk.

For more on how to clone the repo, view [git clone help](https://git-scm.com/docs/git-clone).

Once you have a local copy, run the commands in the following sections from the root of the project tree.

## Overview

Here are the main `make` targets:

- `docker-compose-build` - used for building the development image, which is used by the `docker-compose` target. You can skip this target if you want to use the latest [ghcr.io/ansible/awx_devel:devel](https://github.com/ansible/awx/pkgs/container/awx_devel) image rather than build a new one.
- `docker-compose` - make target for development, passes awx_devel image and tag

Notable files:

- `tools/docker-compose/inventory` file - used to configure the AWX development environment.
- `tools/docker-compose/ansible/migrate.yml` - playbook for migrating data from Local Docker to the Development Environment

### Prerequisites

- [Docker](https://docs.docker.com/engine/installation/) on the host where AWX will be deployed. After installing Docker, the Docker service must be started (depending on your OS, you may have to add the local user that uses Docker to the `docker` group, refer to the documentation for details)
- [Docker Compose](https://docs.docker.com/compose/install/).
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) will need to be installed as we use it to template files needed for the docker-compose.
- OpenSSL.

### Tested Operating Systems

The docker-compose development environment is regularly used and should work on x86_64 systems running:

- Fedora (maintained versions)
- Ubuntu LTS (18, 20)
- Red Hat Enterprise Linux 8, CentOS Stream 8
- macOS 11

Use on other platforms is untested, and may require local changes.

### How to Disable Color?

There are several layers that might apply color:
 - docker compose coloring based on what container log comes from
 - supervisord coloring based on what server it comes from
 - general coloration from Django management commands

These can have color turned off by adding things to the
environment variable to modify the call options.

```
DJANGO_COLORS=nocolor COMPOSE_UP_OPTS="--no-color" SUPERVISOR_ARGS="-n -t" make docker-compose
```

This can be useful if this is ran in CI in any context.

## Starting the Development Environment

### Build the Image

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

> By default, this image will be tagged with your branch name. You can specify a custom tag by setting an environment variable, for example: `DEVEL_IMAGE_NAME=quay.io/your_user/awx_devel:17.0.1`

#### Customizing the Receptor Image

By default, the development environment will use the `devel` image from receptor.
This is used directly in `docker-compose.yml` for the hop nodes.
The receptor binary is also copied over to the main awx_devel image, used in all other AWX nodes.

Because of this, the `RECEPTOR_IMAGE` environment variable must be set when running
both docker-compose-build and docker-compose in order to use the correct receptor in all containers.

If you need to create a new receptor image, you can check out receptor and build it like this:

```bash
CONTAINERCMD=docker TAG=quay.io/ansible/receptor:release_1.1 make container
```

Then that can be used by AWX like this:

```bash
export RECEPTOR_IMAGE=quay.io/ansible/receptor:release_1.1
make docker-compose-build
make docker-compose
```

### Run AWX

##### Start the containers

Run the awx, postgres and redis containers. This utilizes the image built in the previous step, and will automatically start all required services and dependent containers. Once the containers launch, your session will be attached to the awx container, and you'll be able to watch log messages and events in real time. You will see messages from Django and the front end build process.

```bash
$ make docker-compose
```

> The make target assumes that the image you built is tagged with your current branch. This allows you to build images for different contexts or branches. When starting the containers, you can choose a specific branch by setting `COMPOSE_TAG=<branch name> `in your environment. For example, you might be working in a feature branch, but you want to run the containers using the devel image you built previously. To do that, start the containers using the following command: `$ COMPOSE_TAG=devel make docker-compose`

> For running docker-compose detached mode, start the containers using the following command: `$ make docker-compose COMPOSE_UP_OPTS=-d`

###### Solving database-related issues during initial startup

If you have encountered the infinitely-repeating `Waiting for postgres to be ready to accept connections` message during the execution, try to do the following:

1. Stop and delete AWX-related docker containers.
2. Delete all associated docker volumes.
3. Delete all associated docker networks.
4. Repeat the process from scratch.

If you have **only** AWX-related container entities in your system, you can simply stop and delete everything using the following commands:

```bash
docker stop $(docker ps -a -q)
docker system prune -a
docker volume prune
docker network prune
```

##### _(alternative method)_ Spin up a development environment with customized mesh node cluster

A cluster (of containers) with execution nodes and a hop node can be created by the docker-compose Makefile target.
By default, it will create 1 hybrid node.
You can switch the type of AWX nodes between hybrid and control with `MAIN_NODE_TYPE`.

```
MAIN_NODE_TYPE=control EXECUTION_NODE_COUNT=2 COMPOSE_TAG=devel make docker-compose
```

Running the above command will create a cluster of 1 control node, 1 hop node, and 2 execution nodes.
A hop node is automatically created whenever there are 1 or more execution nodes.

The number of nodes can be changed:

```
CONTROL_PLANE_NODE_COUNT=2 EXECUTION_NODE_COUNT=3 COMPOSE_TAG=devel make docker-compose
```

This will spin up a topology represented below.
(names are the receptor node names, which differ from the AWX Instance names and network address in some cases)

```
                                            ┌──────────────┐
                                            │              │
┌──────────────┐                 ┌──────────┤  receptor-1  │
│              │                 │          │              │
│    awx_1     │◄──────────┐     │          └──────────────┘
│              │           │     ▼
└──────┬───────┘    ┌──────┴───────┐        ┌──────────────┐
       │            │              │        │              │
       │            │ receptor-hop │◄───────┤  receptor-2  │
       ▼            │              │        │              │
┌──────────────┐    └──────────────┘        └──────────────┘
│              │                 ▲
│    awx_2     │                 │          ┌──────────────┐
│              │                 │          │              │
└──────────────┘                 └──────────┤  receptor-3  │
                                            │              │
                                            └──────────────┘
```

All execution (`receptor-*`) nodes connect to the hop node.
Only the `awx_1` node connects to the hop node out of the AWX cluster.
`awx_1` connects to `awx_2`, fulfilling the requirement that the AWX cluster is fully connected.

For example, if a job is launched with `awx_2` as the `controller_node` and `receptor-3` as the `execution_node`,
then `awx_2` communicates to `receptor-3` via `awx_1` and then `receptor-hop`.


##### Wait for migrations to complete

The first time you start the environment, database migrations need to run in order to build the PostgreSQL database. It will take few moments, but eventually you will see output in your terminal session that looks like the following:

```bash
awx_1        | Operations to perform:
awx_1        |   Synchronize unmigrated apps: solo, api, staticfiles, debug_toolbar, messages, channels, django_extensions, ui, rest_framework, polymorphic
awx_1        |   Apply all migrations: sso, taggit, sessions, sites, kombu_transport_django, contenttypes, auth, conf, main
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

##### Clean and build the UI

Prerequisites (on your local machine)
- npm
- nodejs

Required versions listed here https://github.com/ansible/ansible-ui/blob/main/README.md

On your local machine (not in awx container)

```bash
make clean/ui ui
```

This will clone the ansible-ui into the `awx/ui/src` directory and build the static files. Then when the containers come up, awx-manage collectstatic will copy those files into the proper place.

You can also use `UI_LOCAL` to build from a locally cloned ansible-ui repo.

See [the ui development documentation](https://github.com/ansible/ansible-ui/blob/main/CONTRIBUTING.md) for more information on using the frontend development, build, and test tooling.

Once migrations are completed and the UI is built, you can begin using AWX. The UI can be reached in your browser at `https://localhost:8043/`, and the API can be found at `https://localhost:8043/api/v2`.

##### Create an admin user

Before you can log into AWX, you need to create an admin user. With this user you will be able to create more users, and begin configuring the server. From within the container shell, run the following command:

```bash
$ docker exec -ti tools_awx_1 awx-manage createsuperuser
```

> Remember the username and password, as you will use them to log into the web interface for the first time.

##### Load demo data

Optionally, you may also want to load some demo data. This will create a demo project, inventory, and job template.

```bash
$ docker exec tools_awx_1 awx-manage create_preload_data
```

> This information will persist in the database running in the `tools_postgres_1` container, until the container is removed. You may periodically need to recreate
> this container, and thus the database, if the database schema changes in an upstream commit.

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

- [Start a shell](#start-a-shell)
- [Start AWX from the container shell](#start-awx-from-the-container-shell)
- [Using Logstash](./docs/logstash.md)
- [Start a Cluster](#start-a-cluster)
- [Start with Minikube](#start-with-minikube)
- [Splunk Integration](#splunk-integration)

### Start a Shell

To run `awx-manage` commands and modify things inside the container, you will want to start a shell session on the _awx_ container. In a new terminal session, use the `docker exec` command to start the shell session:

```bash
(host)$ docker exec -it tools_awx_1 bash
```

This creates a session in the _awx_ containers, just as if you were using `ssh`, and allows you execute commands within the running container.

### Start AWX from the container shell

Often times you'll want to start the development environment without immediately starting all of the services in the _awx_ container, and instead be taken directly to a shell. You can do this with the following:

```bash
(host)$ make docker-compose-test
```

Using `docker exec`, this will create a session in the running _awx_ container, and place you at a command prompt, where you can run shell commands inside the container.

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

### Start a Cluster

Certain features or bugs are only applicable when running a cluster of AWX nodes. To bring up a 3 node cluster development environment simply run the below command.

```bash
(host)$ CONTROL_PLANE_NODE_COUNT=3 make docker-compose
```

`CONTROL_PLANE_NODE_COUNT` is configurable and defaults to 1, effectively a non-clustered AWX.

Note that you may see multiple messages of the form `2021-03-04 20:11:47,666 WARNING [-] awx.main.wsrelay Connection from awx_2 to awx_5 failed: 'Cannot connect to host awx_5:8013 ssl:False [Name or service not known]'.`. This can happen when you bring up a cluster of many nodes, say 10, then you bring up a cluster of less nodes, say 3. In this example, there will be 7 `Instance` records in the database that represent AWX instances. The AWX development environment mimics the VM deployment (vs. kubernetes) and expects the missing nodes to be brought back to healthy by the admin. The warning message you are seeing is all of the AWX nodes trying to connect the websocket backplane. You can manually delete the `Instance` records from the database i.e. `Instance.objects.get(hostname='awx_9').delete()` to stop the warnings.

### Start with Minikube

To bring up a 1 node AWX + minikube that is accessible from AWX run the following.

Start minikube

```bash
(host)$minikube start --cpus=4  --memory=8g --addons=ingress
```

Start AWX

```bash
(host)$ make docker-compose-container-group
```

Alternatively, you can set the env var `MINIKUBE_CONTAINER_GROUP=true` to use the default dev env bring up. his way you can use other env flags like the cluster node count. Set `MINIKUBE_SETUP=true` to make the roles download, install and run minikube for you, but if you run into issues with this just start minikube yourself.

```bash
(host)$ MINIKUBE_CONTAINER_GROUP=true make docker-compose
```

If you want to clean all things once your are done, you can do:

```bash
(host)$ make docker-compose-container-group-clean
```

### Splunk Integration

Splunk is a log aggregation tool that can be used to test AWX with external logging integration. This section describes how to build a reference Splunk instance and plumb it with your AWX for testing purposes.

First, be sure that you have the awx.awx collection installed by running `make install_collection`.

Next, install the splunk.es collection by running `ansible-galaxy collection install splunk.es`.

Anytime you want to run a Splunk instance alongside AWX we can start docker-compose with the SPLUNK option to get a Splunk instance with the command:
```bash
SPLUNK=true make docker-compose
```

Once the containers come up three new ports (8000, 8089 and 9199) should be exposed and the Splunk server should be running on some of those ports (the 9199 will be created later by the plumbing playbook). The first port (8000) is the non-SSL admin port and you can log into splunk with the credentials admin/splunk_admin. The url will be like http://<server>:8000/ this will be referenced below. The 8089 is the API port that the ansible modules will use to connect to and configure splunk. The 9199 port will be used to construct a TCP listener in Splunk that AWX will forward messages to.

Once the containers are up we are ready to configure and plumb Splunk with AWX. To do this we have provided a playbook which will:
* Backup and configure the External Logging adapter in AWX. NOTE: this will back up your existing settings but the password fields can not be backed up through the API, you need a DB backup to recover this.
* Create a TCP port in Splunk for log forwarding

For routing traffic between AWX and Splunk we will use the internal docker compose network. The `Logging Aggregator` will be configured using the internal network machine name of `splunk`.

Once you have have the collections installed (from above) you can run the playbook like:
```bash
export CONTROLLER_USERNAME=<your username>
export CONTROLLER_PASSWORD=<your password>
ansible-playbook tools/docker-compose/ansible/plumb_splunk.yml
```

Once the playbook is done running Splunk should now be setup in your development environment. You can log into the admin console (see above for username/password) and click on "Searching and Reporting" in the left hand navigation. In the search box enter `source="http:tower_logging_collections"` and click search.

### HashiVault Integration

Run a HashiVault container alongside of AWX.

```bash
VAULT=true make docker-compose
```

You can find the initialization data at `tools/docker-compose/_sources/secrets/vault_init.yml`,
This includes the unseal keys and a root token.

You will need to unseal the HashiVault each time the container is started.
The easiest way to do that is to run:
```bash
ansible-playbook tools/docker-compose/ansible/unseal_vault.yml
```
This will perform the unseal and also display the root token for login.

For demo purposes, Vault will be auto-configured to include a Key Value (KV) vault called `my_engine` along with a secret called `my_key` in `/my_engine/my_root/my_folder`.
The secret value is `this_is_the_secret_value`.

To create a secret connected to this vault in AWX you can run the following playbook:
```bash
export CONTROLLER_USERNAME=<your username>
export CONTROLLER_PASSWORD=<your password>
ansible-playbook tools/docker-compose/ansible/plumb_vault.yml
```

This will create the following items in your AWX instance:
* A credential called `Vault Lookup Cred` tied to the vault instance.
* A credential called `Vault UserPass Lookup Cred` tied to the vault instance.
* A custom credential type called `Vault Custom Cred Type`.
* A credential called `Credential From HashiCorp Vault via Token Auth` which is of the created type using the `Vault Lookup Cred` to get the secret.
* A credential called `Credential From HashiCorp Vault via UserPass Auth` which is of the created type using the `Vault Userpass Lookup Cred` to get the secret.

The custom credential type adds a variable when used in a playbook called `the_secret_from_vault`.
If you have a playbook like:
```
---
- name: Show a vault secret
  hosts: localhost
  connection: local
  gather_facts: False
  tasks:
    - debug:
        var: the_secret_from_vault
```

And run it through AWX with the credential `Credential From Vault via Token Auth` tied to it, the debug should result in `this_is_the_secret_value`. If you run it through AWX with the credential `Credential From Vault via Userpass Auth`, the debug should result in `this_is_the_userpass_secret_value`.

### Prometheus and Grafana integration

See docs at https://github.com/ansible/awx/blob/devel/tools/grafana/README.md

### OpenTelemetry Integration

```bash
OTEL=true GRAFANA=true LOKI=true PROMETHEUS=true make docker-compose
```

This will start the sidecar container `tools_otel_1` and configure AWX logging to send to it. The OpenTelemetry Collector is configured to export logs to Loki. Grafana is configured with Loki as a datasource. AWX logs can be viewed in Grafana.

`http://localhost:3001` grafana
