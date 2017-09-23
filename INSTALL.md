# Installing AWX

This document provides a guide for installing AWX.

## Table of contents

- [Getting started](#getting-started)
  - [Clone the repo](#clone-the-repo)
  - [AWX branding](#awx-branding)
  - [Prerequisites](#prerequisites)
  - [AWX Tunables](#awx-tunables)
  - [Choose a deployment platform](#choose-a-deployment-platform)
- [OpenShift](#openshift)
  - [Prerequisites](#prerequisites)
    - [Deploying to Minishift](#deploying-to-minishift)
  - [Pre-build steps](#pre-build-steps)
  - [PostgreSQL](#postgresql)
  - [Start the build](#start-the-build)
  - [Post build](#post-build)
  - [Accessing AWX](#accessing-awx)
- [Docker](#docker)
  - [Prerequisites](#prerequisites-2)
  - [Pre-build steps](#pre-build-steps-1)
    - [Deploying to a remote host](#deploying-to-a-remote-host)
    - [Inventory variables](#inventory-variables)
      - [Docker registry](#docker-registry)
      - [PostgreSQL](#postgresql-1)
      - [Proxy settings](#proxy-settings)
  - [Start the build](#start-the-build-1)
  - [Post build](#post-build-1)
  - [Accessing AWX](#accessing-awx-1)

## Getting started

### Clone the repo

If you have not already done so, you will need to clone, or create a local copy, of the [AWX repo](https://github.com/ansible/awx). For more on how to clone the repo, view [git clone help](https://git-scm.com/docs/git-clone).

Once you have a local copy, run commands within the root of the project tree.

### AWX branding

You can optionally install the AWX branding assets from the [awx-logos repo](https://github.com/ansible/awx-logos). Prior to installing, please review and agree to the [trademark guidelines](https://github.com/ansible/awx-logos/blob/master/TRADEMARKS.md).

To install the assets, clone the `awx-logos` repo so that it is next to your `awx` clone. As you progress through the installation steps, you'll be setting variables in the [inventory](./installer/inventory) file. To include the assets in the build, set `awx_official=true`.

### Prerequisites

Before you can run a deployment, you'll need the following installed in your local environment:

- [Ansible](http://docs.ansible.com/ansible/latest/intro_installation.html) Requires Version 2.3+
- [Docker](https://docs.docker.com/engine/installation/)
- [docker-py](https://github.com/docker/docker-py) Python module
- [GNU Make](https://www.gnu.org/software/make/)
- [Git](https://git-scm.com/)

### AWX Tunables

**TODO** add tunable bits

### Choose a deployment platform

We currently support running AWX as a containerized application using Docker images deployed to either an OpenShift cluster, or a standalone Docker daemon. The remainder of this document will walk you through the process of building the images, and deploying them to either platform.

The [installer](./installer) directory contains an [inventory](./installer/inventory) file, and a playbook, [install.yml](./installer/install.yml). You'll begin by setting variables in the inventory file according to the platform you wish to use, and then you'll start the image build and deployment process by running the playbook.

In the sections below, you'll find deployment details and instructions for each platform. To deploy to Docker, view the [Docker section](#docker), and for OpenShift, view the [OpenShift section](#openshift).

## OpenShift

### Prerequisites

To complete a deployment to OpenShift, you will obviously need access to an OpenShift cluster. For demo and testing purposes, you can use [Minishift](https://github.com/minishift/minishift) to create a single node cluster running inside a virtual machine.

You will also need to have the `oc` command in your PATH. The `install.yml` playbook will call out to `oc` when logging into, and creating objects on the cluster.

#### Deploying to Minishift

Install Minishift by following the [installation guide](https://docs.openshift.org/latest/minishift/getting-started/installing.html).

The Minishift VM contains a Docker daemon, which you can use to build the AWX images. This is generally the approach you should take, and we recommend doing so. To use this instance, run the following command to setup your environment:

```bash
# Set DOCKER environment variable to point to the Minishift VM
$ eval $(minishift docker-env)
```

**Note**

> If you choose to not use the Docker instance running inside the VM, and build the images externally, you will have to enable the OpenShift cluster to access the images. This involves pushing the images to an external Docker registry, and granting the cluster access to it, or exposing the internal registry, and pushing the images into it.

### Pre-build steps

Before starting the build process, review the [inventory](./installer/inventory) file, and uncomment and provide values for the following variables found in the `[all:vars]` section:

*openshift_host*

> IP address or hostname of the OpenShift cluster. If you're using Minishift, this will be the value returned by `minishift ip`.

*awx_openshift_project*

> Name of the OpenShift project that will be created, and used as the namespace for the AWX app. Defaults to *awx*.

*awx_node_port*

> The web server port running inside the AWX pod. Defaults to *30083*.

*openshift_user*

> Username of the OpenShift user that will create the project, and deploy the application. Defaults to *developer*.

*docker_registry*

> IP address and port, or URL, for accessing a registry that the OpenShift cluster can access. Defaults to *172.30.1.1:5000*, the internal registry delivered with Minishift.

*docker_registry_repository*

> Namespace to use when pushing and pulling images to and from the registry. Generally this will match the project name. It defaults to *awx*.

*docker_registry_username*

> Username of the user that will push images to the registry. Will generally match the *openshift_user* value. Defaults to *developer*.

#### PostgreSQL

AWX requires access to a PostgreSQL database, and by default, one will be created and deployed in a pod. The database is configured for persistence and will create a persistent volume claim named `postgresql`. By default it will claim 5GB from the available persistent volume pool. This can be tuned by setting a variable in the inventory file or on the command line during the `ansible-playbook` run.

    ansible-playbook ... -e pg_volume_capacity=n

If you wish to use an external database, in the inventory file, set the value of `pg_hostname`, and update `pg_username`, `pg_password`, `pg_database`, and `pg_port` with the connection information. When setting `pg_hostname` the installer will assume you have configured the database in that location and will not launch the postgresql pod.

### Start the build

To start the build, you will pass two *extra* variables on the command line. The first is *openshift_password*, which is the password for the *openshift_user*, and the second is *docker_registry_password*, which is the password associated with *docker_registry_username*.

If you're using the OpenShift internal registry, then you'll pass an access token for the *docker_registry_password* value, rather than a password. The `oc whoami -t` command will generate the required token, as long as you're logged into the cluster via `oc cluster login`.

To start the build and deployment, run the following:

```bash
# Start the build and deployment
$ ansible-playbook -i inventory install.yml -e openshift_password=developer  -e docker_registry_password=$(oc whoami -t)
```

### Post build

After the playbook run completes, check the status of the deployment by running `oc get pods`:

```bash
# View the running pods
$ oc get pods

NAME                   READY     STATUS    RESTARTS   AGE
awx-3886581826-5mv0l   4/4       Running   0          8s
postgresql-1-l85fh     1/1       Running   0          20m

```

In the above example, the name of the AWX pod is `awx-3886581826-5mv0l`. Before accessing the AWX web interface, setup tasks and database migrations need to complete. These tasks are running in the `awx_task` container inside the AWX pod. To monitor their status, tail the container's STDOUT by running the following command, replacing the AWX pod name with the pod name from your environment:

```bash
# Follow the awx_task log output
$ oc logs -f awx-3886581826-5mv0l -c awx-celery
```

You will see the following indicating that database migrations are running:

```bash
Using /etc/ansible/ansible.cfg as config file
127.0.0.1 | SUCCESS => {
    "changed": false,
    "db": "awx"
}
Operations to perform:
  Synchronize unmigrated apps: solo, api, staticfiles, messages, channels, django_extensions, ui, rest_framework, polymorphic
  Apply all migrations: sso, taggit, sessions, djcelery, sites, kombu_transport_django, social_auth, contenttypes, auth, conf, main
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
  Installing custom SQL...
Running migrations:
  Rendering model states... DONE
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying taggit.0001_initial... OK
  Applying taggit.0002_auto_20150616_2121... OK
  ...
```

When you see output similar to the following, you'll know that database migrations have completed, and you can access the web interface:

```bash
Python 2.7.5 (default, Nov  6 2016, 00:28:07)
[GCC 4.8.5 20150623 (Red Hat 4.8.5-11)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)

>>> <User: admin>
>>> Default organization added.
Demo Credential, Inventory, and Job Template added.
Successfully registered instance awx-3886581826-5mv0l
(changed: True)
Creating instance group tower
Added instance awx-3886581826-5mv0l to tower
```

Once database migrations complete, the web interface will be accessible.

### Accessing AWX

The AWX web interface is running in the AWX pod, behind the `awx-web-svc` service. To view the service, and its port value, run the following command:

```bash
# View available services
$ oc get services

NAME          CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
awx-web-svc   172.30.111.74   <nodes>       8052:30083/TCP   37m
postgresql    172.30.102.9    <none>        5432/TCP         38m
```

The deployment process creates a route, `awx-web-svc`, to expose the service. How the ingres is actually created will vary depending on your environment, and how the cluster is configured. You can view the route, and the external IP address and hostname assigned to it, by running the following command:

```bash
# View available routes
$ oc get routes

NAME          HOST/PORT                             PATH      SERVICES      PORT      TERMINATION   WILDCARD
awx-web-svc   awx-web-svc-awx.192.168.64.2.nip.io             awx-web-svc   http      edge/Allow    None
```

The above example is taken from a Minishift instance. From a web browser, use `https` to access the `HOST/PORT` value from your environment. Using the above example, the URL to access the server would be [https://awx-web-svc-awx.192.168.64.2.nip.io](https://awx-web-svc-awx.192.168.64.2.nip.io).

Once you access the AWX server, you will be prompted with a login dialog. The default administrator username is `admin`, and the password is `password`.

## Docker

### Prerequisites

You will need the following installed on the host where AWX will be deployed:

- [Docker](https://docs.docker.com/engine/installation/)
- [docker-py](https://github.com/docker/docker-py) Python module

### Pre-build steps

#### Deploying to a remote host

By default, the delivered [installer/inventory](./installer/inventory) file will deploy AWX to the local host. It is possible; however, to deploy to a remote host. The [installer/install.yml](./installer/install.yml) playbook can be used to build images on the local host, and ship the built images to, and run deployment tasks on, a remote host. To do this, modify the [installer/inventory](./installer/inventory) file, by commenting out `localhost`, and adding the remote host.

For example, suppose you wish to build images locally on your CI/CD host, and deploy them to a remote host named *awx-server*. To do this, add *awx-server* to the [installer/inventory](./installer/inventory) file, and comment out or remove `localhost`, as demonstrated by the following:

```yaml
# localhost ansible_connection=local
awx-server

[all:vars]
...
```

In the above example, image build tasks will be delegated to `localhost`, which is typically where the clone of the AWX project exists. Built images will be archived, copied to remote host, and imported into the remote Docker image cache. Tasks to start the AWX containers will then execute on the remote host.

**Note**

> You may also want to set additional variables to control how Ansible connects to the host. For more information about this, view [Behavioral Inventory Parameters](http://docs.ansible.com/ansible/latest/intro_inventory.html#id12).

> As mentioned above, in [Prerequisites](#prerequisites-1), the prerequisites are required on the remote host.

> When deploying to a remote host, the playook does not execute tasks with the `become` option. For this reason, make sure the user that connects to the remote host has privileges to run the `docker` command. This typically means that non-privileged users need to be part of the `docker` group.


#### Inventory variables

Before starting the build process, review the [inventory](./installer/inventory) file, and uncomment and provide values for the following variables found in the `[all:vars]` section:

*postgres_data_dir*

> If you're using the default PostgreSQL container (see [PostgreSQL](#postgresql-1) below), provide a path that can be mounted to the container, and where the database can be persisted.

*host_port*

> Provide a port number that can be mapped from the Docker daemon host to the web server running inside the AWX container. Defaults to *80*.


#### Docker registry

If you wish to tag and push built images to a Docker registry, set the following variables in the inventory file:

*docker_registry*

> IP address and port, or URL, for accessing a registry.

*docker_registry_repository*

> Namespace to use when pushing and pulling images to and from the registry. Defaults to *awx*.

*docker_registry_username*

> Username of the user that will push images to the registry. Defaults to *developer*.


#### Proxy settings

*http_proxy*

> IP address and port, or URL, for using an http_proxy.

*https_proxy*

> IP address and port, or URL, for using an https_proxy.

*no_proxy*

> Exclude IP address or URL from the proxy.

#### PostgreSQL

AWX requires access to a PostgreSQL database, and by default, one will be created and deployed in a container, and data will be persisted to a host volume. In this scenario, you must set the value of `postgres_data_dir` to a path that can be mounted to the container. When the container is stopped, the database files will still exist in the specified path.

If you wish to use an external database, in the inventory file, set the value of `pg_hostname`, and update `pg_username`, `pg_password`, `pg_database`, and `pg_port` with the connection information.

### Start the build

If you are not pushing images to a Docker registry, start the build by running the following:

```bash
# Set the working directory to installer
$ cd installer

# Run the Ansible playbook
$ ansible-playbook -i inventory install.yml
```

If you're pushing built images to a repository, then use the `-e` option to pass the registry password as follows, replacing *password* with the password of the username assigned to `docker_registry_username`:

```bash
# Set the working directory to installer
$ cd installer

# Run the Ansible playbook
$ ansible-playbook -i inventory -e docker_registry_password=password install.yml
```

### Post build

After the playbook run completes, Docker will report up to 5 running containers. If you chose to use an existing PostgresSQL database, then it will report 4. You can view the running containers using the `docker ps` command, as follows:

```bash
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                                NAMES
e240ed8209cd        awx_task:1.0.0.8    "/tini -- /bin/sh ..."   2 minutes ago       Up About a minute   8052/tcp                             awx_task
1cfd02601690        awx_web:1.0.0.8     "/tini -- /bin/sh ..."   2 minutes ago       Up About a minute   0.0.0.0:80->8052/tcp                 awx_web
55a552142bcd        memcached:alpine    "docker-entrypoint..."   2 minutes ago       Up 2 minutes        11211/tcp                            memcached
84011c072aad        rabbitmq:3          "docker-entrypoint..."   2 minutes ago       Up 2 minutes        4369/tcp, 5671-5672/tcp, 25672/tcp   rabbitmq
97e196120ab3        postgres:9.6        "docker-entrypoint..."   2 minutes ago       Up 2 minutes        5432/tcp                             postgres
```

Immediately after the containers start, the *awx_task* container will perform required setup tasks, including database migrations. These tasks need to complete before the web interface can be accessed. To monitor the progress, you can follow the container's STDOUT by running the following:

```bash
# Tail the the awx_task log
$ docker logs -f awx_task
```

You will see output similar to the following:

```bash
Using /etc/ansible/ansible.cfg as config file
127.0.0.1 | SUCCESS => {
    "changed": false,
    "db": "awx"
}
Operations to perform:
  Synchronize unmigrated apps: solo, api, staticfiles, messages, channels, django_extensions, ui, rest_framework, polymorphic
  Apply all migrations: sso, taggit, sessions, djcelery, sites, kombu_transport_django, social_auth, contenttypes, auth, conf, main
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
  Installing custom SQL...
Running migrations:
  Rendering model states... DONE
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying taggit.0001_initial... OK
  Applying taggit.0002_auto_20150616_2121... OK
  Applying main.0001_initial... OK
...
```

Once migrations complete, you will see the following log output, indicating that migrations have completed:

```bash
Python 2.7.5 (default, Nov  6 2016, 00:28:07)
[GCC 4.8.5 20150623 (Red Hat 4.8.5-11)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)

>>> <User: admin>
>>> Default organization added.
Demo Credential, Inventory, and Job Template added.
Successfully registered instance awx
(changed: True)
Creating instance group tower
Added instance awx to tower
(changed: True)
...
```

### Accessing AWX

The AWX web server is accessible on the deployment host, using the *host_port* value set in the *inventory* file. The default URL is [http://localhost](http://localhost).

You will prompted with a login dialog. The default administrator username is `admin`, and the password is `password`.
