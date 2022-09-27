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

- `docker-compose-build` - used for building the development image, which is used by the `docker-compose` target
- `docker-compose` - make target for development, passes awx_devel image and tag

Notable files:

- `tools/docker-compose/inventory` file - used to configure the AWX development environment.
- `migrate.yml` - playbook for migrating data from Local Docker to the Development Environment

### Prerequisites

- [Docker](https://docs.docker.com/engine/installation/) on the host where AWX will be deployed. After installing Docker, the Docker service must be started (depending on your OS, you may have to add the local user that uses Docker to the `docker` group, refer to the documentation for details)
- [docker-compose](https://pypi.org/project/docker-compose/) Python module.
  - This also installs the `docker` Python module, which is incompatible with [`docker-py`](https://pypi.org/project/docker-py/). If you have previously installed `docker-py`, please uninstall it.
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

## Configuration

In the [`inventory` file](./inventory), set your `pg_password`, `broadcast_websocket_secret`, `secret_key`, and any other settings you need for your deployment.

AWX requires access to a PostgreSQL database, and by default, one will be created and deployed in a container, and data will be persisted to a docker volume. When the container is stopped, the database files will still exist in the docker volume. An external database can be used by setting the `pg_host`, `pg_hostname`, and `pg_username`.

> If you are coming from a Local Docker installation of AWX, consider migrating your data first, see the [data migration section](#migrating-data-from-local-docker) below.

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


##### _(alternative method)_ Spin up a development environment with customized mesh node cluster

With the introduction of Receptor, a cluster (of containers) with execution nodes and a hop node can be created by the docker-compose Makefile target.
By default, it will create 1 hybrid node, 1 hop node, and 2 execution nodes.
You can switch the type of AWX nodes between hybrid and control with this syntax.

```
MAIN_NODE_TYPE=control COMPOSE_TAG=devel make docker-compose
```

Running the above command will create a cluster of 1 control node, 1 hop node, and 2 execution nodes.

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

##### Clean and build the UI

```bash
$ docker exec tools_awx_1 make clean-ui ui-devel
```

See [the ui development documentation](../../awx/ui/README.md) for more information on using the frontend development, build, and test tooling.

Once migrations are completed and the UI is built, you can begin using AWX. The UI can be reached in your browser at `https://localhost:8043/#/home`, and the API can be found at `https://localhost:8043/api/v2`.

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
- [SAML and OIDC Integration](#saml-and-oidc-integration)
- [OpenLDAP Integration](#openldap-integration)
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

Note that you may see multiple messages of the form `2021-03-04 20:11:47,666 WARNING [-] awx.main.wsbroadcast Connection from awx_2 to awx_5 failed: 'Cannot connect to host awx_5:8013 ssl:False [Name or service not known]'.`. This can happen when you bring up a cluster of many nodes, say 10, then you bring up a cluster of less nodes, say 3. In this example, there will be 7 `Instance` records in the database that represent AWX instances. The AWX development environment mimics the VM deployment (vs. kubernetes) and expects the missing nodes to be brought back to healthy by the admin. The warning message you are seeing is all of the AWX nodes trying to connect the websocket backplane. You can manually delete the `Instance` records from the database i.e. `Instance.objects.get(hostname='awx_9').delete()` to stop the warnings.

### Start with Minikube

To bring up a 1 node AWX + minikube that is accessible from AWX run the following.

```bash
(host)$ make docker-compose-container-group
```

Alternatively, you can set the env var `MINIKUBE_CONTAINER_GROUP=true` to use the default dev env bring up. his way you can use other env flags like the cluster node count.

```bash
(host)$ MINIKUBE_CONTAINER_GROUP=true make docker-compose
```

If you want to clean all things once your are done, you can do:

```bash
(host)$ make docker-compose-container-group-clean
```

### SAML and OIDC Integration
Keycloak can be used as both a SAML and OIDC provider and can be used to test AWX social auth. This section describes how to build a reference Keycloak instance and plumb it with AWX for testing purposes.

First, be sure that you have the awx.awx collection installed by running `make install_collection`.
Next, make sure you have your containers running by running `make docker-compose`.

Note: The following instructions assume we are using the built-in postgres database container. If you are not using the internal database you can use this guide as a reference, updating the database fields as required for your connection.

We are now ready to run two one time commands to build and pre-populate the Keycloak database.

The first one time command will be creating a Keycloak database in your postgres database by running:
```bash
docker exec tools_postgres_1 /usr/bin/psql -U awx --command "create database keycloak with encoding 'UTF8';"
```

After running this command the following message should appear and you should be returned to your prompt:
```base
CREATE DATABASE
```

The second one time command will be to start a Keycloak container to build our admin user; be sure to set pg_username and pg_password to work for you installation. Note: the command below set the username as admin with a password of admin, you can change this if you want. Also, if you are using your own container or have changed the pg_username please update the command accordingly.
```bash
PG_PASSWORD=`cat tools/docker-compose/_sources/secrets/pg_password.yml  | cut -f 2 -d \'`
docker run --rm -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin --net=_sources_default \
           -e DB_VENDOR=postgres -e DB_ADDR=postgres -e DB_DATABASE=keycloak -e DB_USER=awx -e DB_PASSWORD=${PG_PASSWORD} \
           quay.io/keycloak/keycloak:15.0.2
```

Once you see a message like: `WFLYSRV0051: Admin console listening on http://127.0.0.1:9990` you can stop the container.

Now that we have performed the one time setup anytime you want to run a Keycloak instance alongside AWX we can start docker-compose with the KEYCLOAK option to get a Keycloak instance with the command:
```bash
KEYCLOAK=true make docker-compose
```

Go ahead and stop your existing docker-compose run and restart with Keycloak before proceeding to the next steps.

Once the containers come up a new port (8443) should be exposed and the Keycloak interface should be running on that port. Connect to this through a url like `https://localhost:8443` to confirm that Keycloak has stared. If you wanted to login and look at Keycloak itself you could select the "Administration console" link and log into the UI the username/password set in the previous `docker run` command. For more information about Keycloak and links to their documentation see their project at https://github.com/keycloak/keycloak.

Now we are ready to configure and plumb Keycloak with AWX. To do this we have provided a playbook which will:
* Create a certificate for SAML data exchange between Keycloak and AWX.
* Create a realm in Keycloak with a client for AWX via SAML and OIDC and 3 users.
* Backup and configure the SMAL and OIDC adapter in AWX. NOTE: the private key of any existing SAML or OIDC adapters can not be backed up through the API, you need a DB backup to recover this.

Before we can run the playbook we need to understand that SAML works by sending redirects between AWX and Keycloak through the browser. Because of this we have to tell both AWX and Keycloak how they will construct the redirect URLs. On the Keycloak side, this is done within the realm configuration and on the AWX side its done through the SAML settings. The playbook requires a variable called `container_reference` to be set. The container_reference variable needs to be how your browser will be able to talk to the running containers.  Here are some examples of how to choose a proper container_reference.
* If you develop on a mac which runs a Fedora VM which has AWX running within that and the browser you use to access AWX runs on the mac. The the VM with the container has its own IP that is mapped to a name like `tower.home.net`. In this scenario your "container_reference" could be either the IP of the VM or the tower.home.net friendly name.
* If you are on a Fedora work station running AWX and also using a browser on your workstation you could use localhost, your work stations IP or hostname as the container_reference.

In addition, OIDC works similar but slightly differently. OIDC has browser redirection but OIDC will also communicate from the AWX docker instance to the Keycloak docker instance directly. Any hostnames you might have are likely not propagated down into the AWX container. So we need a method for both the browser and AWX container to talk to Keycloak. For this we will likely use your machines IP address. This can be passed in as a variable called `oidc_reference`. If unset this will default to container_reference which may be viable for some configurations.

In addition to container_reference, there are some additional variables which you can override if you need/choose to do so. Here are their names and default values:
```yaml
    keycloak_user: admin
    keycloak_pass: admin
    cert_subject:  "/C=US/ST=NC/L=Durham/O=awx/CN="
```

* keycloak_(user|pass) need to change if you modified the user when starting the initial container above.
* cert_subject will be the subject line of the certificate shared between AWX and keycloak you can change this if you like or just use the defaults.

To override any of the variables above you can add more `-e` arguments to the playbook run below. For example, if you simply need to change the `keycloak_pass` add the argument `-e keycloak_pass=my_secret_pass` to the following ansible-playbook command.

In addition, you may need to override the username or password to get into your AWX instance. We log into AWX in order to read and write the SAML and OIDC settings. This can be done in several ways because we are using the awx.awx collection. The easiest way is to set environment variables such as `CONTROLLER_USERNAME`. See the awx.awx documentation for more information on setting environment variables. In the example provided below we are showing an example of specifying a username/password for authentication.

Now that we have all of our variables covered we can run the playbook like:
```bash
export CONTROLLER_USERNAME=<your username>
export CONTROLLER_PASSWORD=<your password>
ansible-playbook tools/docker-compose/ansible/plumb_keycloak.yml -e container_reference=<your container_reference here> -e oidc_reference=<your oidc reference>
```

Once the playbook is done running both SAML and OIDC should now be setup in your development environment. This realm has three users with the following username/passwords:
1. awx_unpriv:unpriv123
2. awx_admin:admin123
3. awx_auditor:audit123

The first account is a normal user. The second account has the SMAL attribute is_superuser set in Keycloak so will be a super user in AWX if logged in through SAML. The third account has the SAML is_system_auditor attribute in Keycloak so it will be a system auditor in AWX if logged in through SAML. To log in with one of these Keycloak users go to the AWX login screen and click the small "Sign In With SAML Keycloak" button at the bottom of the login box.

Note: The OIDC adapter performs authentication only, not authorization. So any user created in AWX will not have any permissions on it at all.

If you Keycloak configuration is not working and you need to rerun the playbook to try a different `container_reference` or `oidc_reference` you can log into the Keycloak admin console on port 8443 and select the AWX realm in the upper left drop down. Then make sure you are on "Ream Settings" in the Configure menu option and click the trash can next to AWX in the main page window pane. This will completely remove the AWX ream (which has both SAML and OIDC settings) enabling you to re-run the plumb playbook.

### OpenLDAP Integration

OpenLDAP is an LDAP provider that can be used to test AWX with LDAP integration. This section describes how to build a reference OpenLDAP instance and plumb it with your AWX for testing purposes.

First, be sure that you have the awx.awx collection installed by running `make install_collection`.

Anytime you want to run an OpenLDAP instance alongside AWX we can start docker-compose with the LDAP option to get an LDAP instance with the command:
```bash
LDAP=true make docker-compose
```

Once the containers come up two new ports (389, 636) should be exposed and the LDAP server should be running on those ports. The first port (389) is non-SSL and the second port (636) is SSL enabled.

Now we are ready to configure and plumb OpenLDAP with AWX. To do this we have provided a playbook which will:
* Backup and configure the LDAP adapter in AWX. NOTE: this will back up your existing settings but the password fields can not be backed up through the API, you need a DB backup to recover this.

Note: The default configuration will utilize the non-tls connection. If you want to use the tls configuration you will need to work through TLS negotiation issues because the LDAP server is using a self signed certificate.

Before we can run the playbook we need to understand that LDAP will be communicated to from within the AWX container. Because of this, we have to tell AWX how to route traffic to the LDAP container through the `LDAP Server URI` settings. The playbook requires a variable called container_reference to be set. The container_reference variable needs to be how your AWX container will be able to talk to the LDAP container. See the SAML section for some examples for how to select a `container_reference`.

Once you have your container reference you can run the playbook like:
```bash
export CONTROLLER_USERNAME=<your username>
export CONTROLLER_PASSWORD=<your password>
ansible-playbook tools/docker-compose/ansible/plumb_ldap.yml -e container_reference=<your container_reference here>
```


Once the playbook is done running LDAP should now be setup in your development environment. This realm has four users with the following username/passwords:
1. awx_ldap_unpriv:unpriv123
2. awx_ldap_admin:admin123
3. awx_ldap_auditor:audit123
4. awx_ldap_org_admin:orgadmin123

The first account is a normal user. The second account will be a super user in AWX. The third account will be a system auditor in AWX. The fourth account is an org admin. All users belong to an org called "LDAP Organization". To log in with one of these users go to the AWX login screen enter the username/password.


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


### Prometheus and Grafana integration

See docs at https://github.com/ansible/awx/blob/devel/tools/grafana/README.md
