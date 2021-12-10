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

- `tools/docker-compose/inventory` file - used to configure the local AWX development deployment
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

##### Keycloak Integration
The following instructions assume we are using the built in postgres database container. If you are not using the internal database you can use this guide as a reference, updating the database fields as required for your connection.

To stand up a Keycloak integration with your existing AWX instance start by creating a Keycloak database in your postgres database by running:
```bash
docker exec tools_postgres_1 /usr/bin/psql -U awx --command "create database keycloak with encoding 'UTF8';"
```

Now that the database is ready we will start a Keycloak container to build our admin user. Note, the command below set the username as admin with a password of admin. This can be changed if you want.
```bash
docker run -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin --net=_sources_default \
           -e DB_VENDOR=postgres -e DB_ADDR=postgres -e DB_DATABASE=keycloak -e DB_USER=<pg_username> -e DB_PASSWORD=<pg_password> \
           quay.io/keycloak/keycloak:15.0.2
```

Once you see a message like: `WFLYSRV0051: Admin console listening on http://127.0.0.1:9990` you can stop the container.

Now we can restart docker-compose with the KEYCLOAK option to get a Keycloak instance with the command:
```bash
KEYCLOAK=true make docker-compose
```

Once the containers come up a new port (8443) should be exposed and the Keycloak interface should be running on that port. Connect to this interface and select the "Administration console" link. Log into the UI the username/password set in the previous `docker run` command.

Within the UI we are going to import a realm. A realm is a logical section of Keycloak and can be imported through the UI by providing a json formatted file. We have a sample file for the import but it needs a little work before it can be imported into Keycloak. In order to be able to properly import the file we need to understand that SAML works by sending redirects between AWX and Keycloak through the browser. Because of this we have to tell both AWX and Keycloak how they will construct the redirect URLs. On the Keycloak side, this is done within the realm configuration. In the provided Keycloak template we have a place holder for the redirect URL name as `{{ awx_hostname }}`. So the first step to importing the realm is populating our sample file with the appropriate redirect URL. To do this run the following command with your container reference (see below for examples):
```bash
ansible -m template -a 'dest=tools/docker-compose/keycloak.awx.realm.json src=tools/docker-compose/keycloak.awx.realm.json.j2' -e awx_hostname=<container reference> localhost
```

Here are some examples of how to choose a proper container reference.
* I develop on a mac which runs a Fedora VM which has Ansible running within that and the browser I use to access AWX runs on the mac. The container has its own IP that I have mapped to a name like `tower.home.net`. So my "container reference" could be either the IP of the VM or the tower.home.net friendly name.
* If you are on a Fedora work station running AWX and also using a browser on your workstation you could use localhost, your work stations IP or hostname as the container reference. 

Now that you have templated out the realm file we can import it from the UI with the following process:
1. On the left hand menu hover over the drop down that says `Master` and select the `Add Realm` button.
2. In the `Name` field enter a name of `awx` and select the create button. This will create a new initialized default realm for you.
3. In the left hand menu validate that the `awx` realm is selected and then click on the `Import` link (first from bottom).
3. On the import screen click on the `Select file` button and select the rendered template from the previous step. This will show you what you are about to import:
  1. 3 users
  2. 1 client
  3. 1 realm role
4. Click the `Import` button and review the summary table which should look like: ```
ADDED	CLIENT	<container reference>:8043	cd5d4ae2-52d3-4f2f-b3d7-9ab2d8cbca7f
ADDED	REALM_ROLE	default-roles-awx realm	dda55fbb-6ee5-4fe9-b9ff-6ecaba471a87
ADDED	USER	awx_auditor	4ecdbc31-73cf-4819-b60a-3fc25130cd17
ADDED	USER	awx_admin	e584a1db-9b06-4bd7-86b2-fa00abc0aae5
ADDED	USER	awx_unpriv	febd4e9e-7b65-47c2-958a-5a4fc4a03438
```
5. Next click on `Realm Settings` in the left hand menu (top item).
6. Click on the `Keys` tab.
7. Click on the `Providers` tab.
8. Click the delete button next to all of the providers. Note: there has to be at least one provider so it will not let you delete the last one.
9. In `Add Keystore...` drop down at the top of the table select `RSA`.
  1. In the `Console Display Name` enter "awx_provider".
  2. In the `Private RSA Key` field click the `Select File` button and pick the file tools/docker-compose/keycloak.key file.
  3. In the `X509 Certificate` field click the `Select File` button and pick the file tools/docker-compose/keycloak.cert file.
  4. Click the `Save` button
10. In the bread crumb link (under the tabs) click on `Keystores` and delete the last provider that is not the `awx_provider`.
11. Click `Client Scopes` in the left hand menu.
12. Click on `role_list` scope.
13. Click on the `Mappers` tab.
14. Click on the `role list` mapper.
15. Change the `Single Role Attribute` to On and click the `Save` button.

Now that are realm is populated and configured we can configure the SAML adapter within AWX. Be sure to backup any existing SAML configuration you may already have. This can be achieved by going to https://<container reference>:8043/api/v2/settings/saml/ and making a copy of the returned JSON payload. To configure a connection to Keycloak you can post the following payload:
```
{
    "SAML_AUTO_CREATE_OBJECTS": true,
    "SOCIAL_AUTH_SAML_SP_ENTITY_ID": "<container reference>:8043",
    "SOCIAL_AUTH_SAML_SP_PUBLIC_CERT": "-----BEGIN CERTIFICATE-----\nMIIDWTCCAkGgAwIBAgIUGUvC3ctqfaD7b3y8J3hVlmf21tgwDQYJKoZIhvcNAQEL\nBQAwPDELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAk1BMQwwCgYDVQQHDANTd2sxEjAQ\nBgNVBAoMCVdlc3Rpd2FyZTAeFw0yMTExMzAyMDU0NDVaFw0yMjExMzAyMDU0NDVa\nMDwxCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJNQTEMMAoGA1UEBwwDU3drMRIwEAYD\nVQQKDAlXZXN0aXdhcmUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDt\nQCFwAD0/hoWLsRuzS1JvuFhCttPAxHIVVt5Z82LbHWo8PleLotQSVK7DKDDJzR7j\nHjVpxsKU7bPgWFTwin6u2QRm44xux2rFSglHm4EP/dc9gswGL5Jisl6am5eLb2/6\ntMXkKc1Yairk0FWATighU2zsOyBu8yAKFv13PxbztN+S6qrtbEtQrfg+mYYwNZrI\nP1zTNxXtild1C5ZsgrBuqw9OYusC4BpOn0mNap9KT/OgYmoWV/uRgSqlWK1u8pNn\nXjsi70vxOVfSzzZDBJ62/8hVkzai7SVZYbYAWEPeRtZjKqjXu5QHgYR9WPIlMWoK\nhk5fAa8b6RluWojcdx4/AgMBAAGjUzBRMB0GA1UdDgQWBBSMnW3gEXWdMazztI8T\nIX6/gJYrEjAfBgNVHSMEGDAWgBSMnW3gEXWdMazztI8TIX6/gJYrEjAPBgNVHRMB\nAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQANOAlXNZIjxbY+GBwFTme02nSJ\ngoy0W8xEuzrdNdhWjxKksSossq1FxreaJkBX1unx2Q12aJcimipvAM+c4ymZABZG\nkS6xMO/rT8M23YCcVVOF4tsgdtwe85Z85qX8XfzDfxaT51wqSCeOegl0EiWX8AZT\nELVxISxqOFFvZM8z9nIxMG/YhlosebwdWEtMaYYPxjtSFI9UTv4nndbAYAxfcYmj\neCFRny06sj5+V4/28N+G4TrQ5d0eopNwhvbozbTGB92kp+yQvAlAt6+GANAXxKtL\nw04kaxTpfQvCwVl+jZiE7H2jxeb5Hx/9wIp5NNstcHkUIJEBqbmY9/p5hrNI\n-----END CERTIFICATE-----",
    "SOCIAL_AUTH_SAML_SP_PRIVATE_KEY": "$encrypted$",
    "SOCIAL_AUTH_SAML_ORG_INFO": {
        "en-US": {
            "url": "https://<container reference>:8443",
            "name": "Keycloak",
            "displayname": "Keycloak Solutions Engineering"
        }
    },
    "SOCIAL_AUTH_SAML_TECHNICAL_CONTACT": {
        "givenName": "Me Myself",
        "emailAddress": "noone@nowhere.com"
    },
    "SOCIAL_AUTH_SAML_SUPPORT_CONTACT": {
        "givenName": "Me Myself",
        "emailAddress": "noone@nowhere.com"
    },
    "SOCIAL_AUTH_SAML_ENABLED_IDPS": {
        "Keycloak": {
            "attr_user_permanent_id": "name_id",
            "entity_id": "https://<container reference>:8443/auth/realms/awx",
            "attr_groups": "groups",
            "url": "https://<container reference>:8443/auth/realms/awx/protocol/saml",
            "attr_first_name": "first_name",
            "x509cert": "-----BEGIN CERTIFICATE-----MIIDWTCCAkGgAwIBAgIUGUvC3ctqfaD7b3y8J3hVlmf21tgwDQYJKoZIhvcNAQELBQAwPDELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAk1BMQwwCgYDVQQHDANTd2sxEjAQBgNVBAoMCVdlc3Rpd2FyZTAeFw0yMTExMzAyMDU0NDVaFw0yMjExMzAyMDU0NDVaMDwxCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJNQTEMMAoGA1UEBwwDU3drMRIwEAYDVQQKDAlXZXN0aXdhcmUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDtQCFwAD0/hoWLsRuzS1JvuFhCttPAxHIVVt5Z82LbHWo8PleLotQSVK7DKDDJzR7jHjVpxsKU7bPgWFTwin6u2QRm44xux2rFSglHm4EP/dc9gswGL5Jisl6am5eLb2/6tMXkKc1Yairk0FWATighU2zsOyBu8yAKFv13PxbztN+S6qrtbEtQrfg+mYYwNZrIP1zTNxXtild1C5ZsgrBuqw9OYusC4BpOn0mNap9KT/OgYmoWV/uRgSqlWK1u8pNnXjsi70vxOVfSzzZDBJ62/8hVkzai7SVZYbYAWEPeRtZjKqjXu5QHgYR9WPIlMWoKhk5fAa8b6RluWojcdx4/AgMBAAGjUzBRMB0GA1UdDgQWBBSMnW3gEXWdMazztI8TIX6/gJYrEjAfBgNVHSMEGDAWgBSMnW3gEXWdMazztI8TIX6/gJYrEjAPBgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQANOAlXNZIjxbY+GBwFTme02nSJgoy0W8xEuzrdNdhWjxKksSossq1FxreaJkBX1unx2Q12aJcimipvAM+c4ymZABZGkS6xMO/rT8M23YCcVVOF4tsgdtwe85Z85qX8XfzDfxaT51wqSCeOegl0EiWX8AZTELVxISxqOFFvZM8z9nIxMG/YhlosebwdWEtMaYYPxjtSFI9UTv4nndbAYAxfcYmjeCFRny06sj5+V4/28N+G4TrQ5d0eopNwhvbozbTGB92kp+yQvAlAt6+GANAXxKtLw04kaxTpfQvCwVl+jZiE7H2jxeb5Hx/9wIp5NNstcHkUIJEBqbmY9/p5hrNI-----END CERTIFICATE-----",
            "attr_email": "email",
            "attr_last_name": "last_name",
            "attr_username": "username"
        }
    },
    "SOCIAL_AUTH_SAML_SECURITY_CONFIG": {
        "requestedAuthnContext": false
    },
    "SOCIAL_AUTH_SAML_SP_EXTRA": null,
    "SOCIAL_AUTH_SAML_EXTRA_DATA": null,
    "SOCIAL_AUTH_SAML_ORGANIZATION_MAP": {
        "Default": {
            "users": true
        }
    },
    "SOCIAL_AUTH_SAML_TEAM_MAP": null,
    "SOCIAL_AUTH_SAML_ORGANIZATION_ATTR": {},
    "SOCIAL_AUTH_SAML_TEAM_ATTR": {},
    "SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR": {
        "is_superuser_attr": "is_superuser",
        "is_system_auditor_attr": "is_system_auditor"
    }
}
```

SAML should now be setup in your development environment. This realm has three users with the following username/passwords:
1. awx_unpriv:unpriv123
2. awx_admin:admin123
3. awx_auditor:audit123

The first account is a normal user. The second account has the attribute is_superuser set in Keycloak so will be a super user in AWX. The third account has the is_system_auditor attribute in Keycloak so it will be a system auditor in AWX. To log in with one of these Keycloak users go to the AWX login screen and click the small "Sign In With SAML Keycloak" button at the bottom of the login box.


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
