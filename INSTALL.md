# Installing AWX

This document provides instructions for installing AWX on the following platforms:

- [OpenShift container platform](#openshift)
- [Standalone Docker daemon](#docker)

It is intended to be a guide only. The instructions and examples that follow enable you to build a working AWX server. However, this document makes no guarantees regarding the production worthiness of the resulting server.


## OpenShift

The [installer](./installer) directory contains an Ansible playbook, inventory file, and roles for deploying AWX to an OpenShift cluster. The playbook automates the process of building AWX, creating container images, and deploying the application.

### Prerequisites

Before running the deployment for the first time, you'll need to install the following:

- [Ansible](http://docs.ansible.com/ansible/latest/intro_installation.html)
- gettext package for your platform (See [Installing gettext](#installing-gettext))
- [Docker](https://docs.docker.com/engine/installation/)
- Access to an OpenShift cluster (See [Using Minishift](#using-minishift))

#### Installing gettext

On Fedora / CentOS / RHEL:

```bash
$ yum install gettext
```

On macOS:

```bash
$ brew install gettext
$ brew link gettext --force 
```

#### Using Minishift

If you do not have access to an OpenShift cluster, you can install [Minishift](https://github.com/minishift/minishift), and create a single node cluster running inside a virtual machine. It's a convenient way to create a demo environment, suitable for trying out AWX.
 
Once you have Minishift running, you can optionally use the Docker daemon that runs inside the virtual machine, rather than running a second Docker daemon (or Docker for Mac) on your development host. The following will set your environment to use it:
 
```bash
$ minishift $(docker-env)
``` 

### Pre-build Steps

Before kicking off the build, review the [inventory](./installer/inventory) file, and uncomment and provide values for the following variables within the `[all:vars]` section:

**openshift_host**

> IP address or hostname of the OpenShift cluster. If you're using Minishift, this will be the value returned by `minishift ip`.
    
**awx_openshift_project**

> Name of the OpenShift project that will be created, and used as the namespace for the AWX app. Defaults to *awx*.  

**openshift_user**

> Username of the OpenShift user that will create the project, and deploy the application. Defaults to *developer*.

**docker_registry**

> IP address and port, or URL, for accessing a registry that the OpenShift cluster can access. Defaults to *172.30.1.1:5000*, the internal registry delivered with Minishift. 

**docker_registry_repository** 

> Namespace to use when pushing and pulling images to and from the registry. Generally this will match the project name. It defaults to *awx*.

**docker_registry_username**

> Username of the user that will push images to the registry. Will generally match the *openshift_user* value. Defaults to *developer*.

### PostgreSQL

**TODO**

Add notes regarding optional Postgres service here. 


### Start the build

To start the build, you will pass in two *extra* variables on the command line. The first is *openshift_password*, which you will set to the password of the user that will deploy the app. This is the same user you specified for the value of *openshsift_user*

The second variable is *docker_registry_password*. This is the password of the user that will push images to the registry. It's the same user you specified for *docker_registry_username* above.

If you're using Mnishift, and the internal registry, then you'll pass an access token for the *docker_registry_token* value, rather than a password. The `oc whoami -t` command will generate the required token, as long as you're logged into the cluster via `oc cluster login` as the user that will access the registry.

Here's the build command to run, if you're using Minishift, and the internal registry:

```bash
$ ansible-playbook -i inventory install.yml -e openshift_password=developer  -e docker_registry_password=$(oc whoami -t) 
```

### Post build, and accessing AWX

Once the build completes, log into the OpenShift console and view the project. For Minishift users, access the console with the following command:

```bash
$ open https://$(minishift ip):8443
```

Open the `awx` project. Assuming you chose to use the PostgreSQL service, you'll see two pods running: *postgresql* and *awx*. The web server is running inside the *awx* pod. To access it, click on *Applications*, and choose *Routes* from the menu. You'll see a route named *awx-web-svc*, click on the highlighted URL in the second column, under *Hostname*. This will open the AWX login dialog. The username is *admin*, and the password is *password*.

## Docker

**TODO**

Document Docker deployment here.
