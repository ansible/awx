# Running Development Environment in Kubernetes

## Start Minikube

If you do not already have Minikube, install it from:
https://minikube.sigs.k8s.io/docs/start/

Note: This environment has only been tested on Linux.

```
$ minikube start \
    --mount \
    --mount-string="/path/to/awx:/awx_devel" \
    --cpus=4 \
    --memory=8g \
    --addons=ingress
```

### Verify

Ensure that your AWX source code is properly mounted inside of the minikube node:

```
$ minikube ssh
$ ls -la /awx_devel
```

## Deploy the AWX Operator

Clone the [awx-operator](https://github.com/ansible/awx-operator).

For the following playbooks to work, you will need to:

```
$ pip install openshift
```

If you are not changing any code in the operator itself, simply run:

```
$ ansible-playbook ansible/deploy-operator.yml
```

If making changes to the operator itself, run the following command in the root
of the awx-operator repo. If not, continue to the next section.

### Building and Deploying a Custom AWX Operator Image

```
$ operator-sdk build quay.io/<username>/awx-operator
$ docker push quay.io/<username>/awx-operator
$ ansible-playbook ansible/deploy-operator.yml \
    -e pull_policy=Always \
    -e operator_image=quay.io/<username>/awx-operator \
    -e operator_version=latest
```

## Deploy AWX into Minikube using the AWX Operator

If have have not made any changes to the AWX Dockerfile, run the following
command. If you need to test out changes to the Dockerfile, see the 
"Custom AWX Development Image for Kubernetes" section below.

In the root of awx-operator:

```
$ ansible-playbook ansible/instantiate-awx-deployment.yml \
    -e development_mode=yes \
    -e tower_image=gcr.io/ansible-tower-engineering/awx_kube_devel:devel \
    -e tower_image_pull_policy=Always \
    -e tower_ingress_type=ingress
```

### Custom AWX Development Image for Kubernetes

I have found `minikube cache add` to be unacceptably slow for larger images such
as this. A faster workflow involves building the image and pushing it to a
registry:

In the root of the AWX repo:

```
$ make awx-kube-dev-build
$ docker push gcr.io/ansible-tower-engineering/awx_kube_devel:${COMPOSE_TAG}
```

In the root of awx-operator:

```
$ ansible-playbook ansible/instantiate-awx-deployment.yml \
    -e development_mode=yes \
    -e tower_image=gcr.io/ansible-tower-engineering/awx_kube_devel:${COMPOSE_TAG} \
    -e tower_image_pull_policy=Always \
    -e tower_ingress_type=ingress
```

To iterate on changes to the Dockerfile, rebuild and push the image, then delete
the AWX Pod. A new Pod will respawn with the latest revision. 

## Accessing AWX

```
$ minikube service awx-service --url
```
