Table of Contents
=================

   * [Installing AWX](#installing-awx)
      * [The AWX Operator](#the-awx-operator)
         * [Quickstart with minikube](#quickstart-with-minikube)
            * [Starting minikube](#starting-minikube)
            * [Deploying the AWX Operator](#deploying-the-awx-operator)
               * [Verifying the Operator Deployment](#verifying-the-operator-deployment)
            * [Deploy AWX](#deploy-awx)
               * [Accessing AWX](#accessing-awx)
   * [Installing the AWX CLI](#installing-the-awx-cli)
      * [Building the CLI Documentation](#building-the-cli-documentation)


# Installing AWX

:warning: NOTE |
--- |
If you're installing an older release of AWX (prior to 18.0), these instructions have changed.  Take a look at your version specific instructions, e.g., for AWX 17.0.1, see: [https://github.com/ansible/awx/blob/17.0.1/INSTALL.md](https://github.com/ansible/awx/blob/17.0.1/INSTALL.md)
If you're attempting to migrate an old kubernetes or openshift installation, see: [Migrating data from an old AWX instance](https://github.com/ansible/awx-operator#migrating-data-from-an-old-awx-instance)|
If you're attempting to migrate an older Docker-based AWX installation, see: [Migrating Data from Local Docker](https://github.com/ansible/awx/blob/devel/tools/docker-compose/docs/data_migration.md) |

## The AWX Operator

Starting in version 18.0, the [AWX Operator](https://github.com/ansible/awx-operator) is the preferred way to install AWX.  If you want to deploy AWX to Openshift or Kubernetes (not locally), please see the [README.md](https://github.com/ansible/awx-operator#README.md) in the awx-operator repo.  

AWX can also alternatively be installed and [run in Docker](./tools/docker-compose/README.md), but this install path is only recommended for development/test-oriented deployments, and has no official published release.

### Quickstart with minikube

If you don't have an existing OpenShift or Kubernetes cluster, minikube is a fast and easy way to get up and running.

To install minikube, follow the steps in their [documentation](https://minikube.sigs.k8s.io/docs/start/).

#### Starting minikube

Once you have installed minikube, run the following command to start it. You may wish to customize these options.

```
$ minikube start --cpus=4 --memory=8g --addons=ingress
```

#### Deploying the AWX Operator

For a comprehensive overview of features, see [README.md](https://github.com/ansible/awx-operator/blob/devel/README.md) in the awx-operator repo. The following steps are the bare minimum to get AWX up and running. 

```
$ minikube kubectl -- apply -f https://raw.githubusercontent.com/ansible/awx-operator/devel/deploy/awx-operator.yaml
```

##### Verifying the Operator Deployment

After a few seconds, the operator should be up and running. Verify it by running the following command:

```
$ minikube kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
awx-operator-7c78bfbfd-xb6th   1/1     Running   0          11s
```

#### Deploy AWX

Once the Operator is running, you can now deploy AWX by creating a simple YAML file:

```
$ cat myawx.yml
---
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx
spec:
  tower_ingress_type: Ingress
```

And then creating the AWX object in the Kubernetes API:

```
$ minikube kubectl apply -- -f myawx.yml
awx.awx.ansible.com/awx created
```

After creating the AWX object in the Kubernetes API, the operator will begin running its reconciliation loop. 

To see what's going on, you can tail the logs of the operator pod (note that your pod name will be different):

```
$ minikube kubectl logs -- -f awx-operator-7c78bfbfd-xb6th
```

After a few seconds, you will see the database and application pods show up. On a fresh system, it may take a few minutes for the container images to download.

```
$ minikube kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
awx-5ffbfd489c-bvtvf           3/3     Running   0          2m54s
awx-operator-7c78bfbfd-xb6th   1/1     Running   0          6m42s
awx-postgres-0                 1/1     Running   0          2m58s
```

##### Accessing AWX

To access the AWX UI, you'll need to grab the service url from minikube:

```
$ minikube service awx-service --url
http://192.168.59.2:31868
```

On fresh installs, you will see the "AWX is currently upgrading." page until database migrations finish.

Once you are redirected to the login screen, you can now log in by obtaining the generated admin password (note: do not copy the trailing `%`):

```
$ minikube kubectl -- get secret awx-admin-password -o jsonpath='{.data.password}' | base64 --decode
b6ChwVmqEiAsil2KSpH4xGaZPeZvWnWj%
```

Now you can log in at the URL above with the username "admin" and the password above. Happy Automating!


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
