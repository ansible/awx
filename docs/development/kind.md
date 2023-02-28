# Running Development Environment in Kubernetes using Kind Cluster

## Start Kind Cluster
Note: This environment has been tested on MacOS and Fedora with Docker.

If you do not already have Kind, install it from:
https://kind.sigs.k8s.io/docs/user/quick-start/

Create Kind cluster config file
```yml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraMounts:
  - hostPath: /path/to/awx
    containerPath: /awx_devel
  extraPortMappings:
  - containerPort: 30080
    hostPort: 30080
```

Start Kind cluster
```bash
 kind create cluster --config kind-cluster.yaml
```

Verify AWX source tree is mounted in the kind-control-plane container
```bash
 docker exec -it kind-control-plane ls /awx_devel
```

## Deploy the AWX Operator

Clone the [awx-operator](https://github.com/ansible/awx-operator).

For the following playbooks to work, you will need to:

```bash
 pip install openshift
```

If you are not changing any code in the operator itself, git checkout the latest version from https://github.com/ansible/awx-operator/releases, and then follow the instructions in the awx-operator [README](https://github.com/ansible/awx-operator#basic-install).

If making changes to the operator itself, run the following command in the root
of the awx-operator repo. If not, continue to the next section.

### Building and Deploying a Custom AWX Operator Image

```bash
# in awx-operator repo on the branch you want to use
 export IMAGE_TAG_BASE=quay.io/<username>/awx-operator
 make docker-build docker-push deploy
```

Check the operator deployment
```bash
 kubectl get deployments
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
awx-operator-controller-manager   1/1     1            1           16h
```

## Deploy AWX into Kind Cluster using the AWX Operator

If you have not made any changes to the AWX Dockerfile, run the following
command. If you need to test out changes to the Dockerfile, see the
"Custom AWX Development Image for Kubernetes" section below.

In the root of awx-operator:

```bash
 ansible-playbook ansible/instantiate-awx-deployment.yml \
    -e development_mode=yes \
    -e image=ghcr.io/ansible/awx_kube_devel \
    -e image_version=devel \
    -e image_pull_policy=Always \
    -e service_type=nodeport \
    -e namespace=awx \
    -e nodeport_port=30080
```
Check the operator with the following commands:

```bash
# Check the operator deployment
 kubectl get deployments
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
awx                               1/1     1            1           16h
awx-operator-controller-manager   1/1     1            1           16h

 kubectl get pods
NAME                                              READY   STATUS    RESTARTS   AGE
awx-operator-controller-manager-b775bfc7c-fn995   2/2     Running   0          16h
```

If there are errors in the image pull, check that it is using the right tag. You can update the tag that it will pull by editing the deployment.

### Custom AWX Development Image for Kubernetes

Set these environmental variables before starting:
```bash
export DEV_DOCKER_TAG_BASE=quay.io/<USERNAME>
export COMPOSE_TAG=<IMAGE_TAG>
```
In the root of the AWX repo:

```bash
make awx-kube-dev-build
docker push $DEV_DOCKER_TAG_BASE/awx_kube_devel:$COMPOSE_TAG
```

In the root of awx-operator:

```bash
 ansible-playbook ansible/instantiate-awx-deployment.yml \
    -e development_mode=yes \
    -e image=$DEV_DOCKER_TAG_BASE/awx_kube_devel \
    -e image_version=$COMPOSE_TAG \
    -e image_pull_policy=Always \
    -e service_type=nodeport \
    -e namespace=$NAMESPACE
```

To iterate on changes to the Dockerfile, rebuild and push the image, then delete
the AWX Pod. A new Pod will respawn with the latest revision.

## Accessing AWX

To access via the web browser, use the following URL:
```
http://localhost:30080
```

To retrieve your admin password
```bash
 kubectl get secrets awx-admin-password -o json | jq '.data.password' | xargs | base64 -d
```

To tail logs from the task containers
```bash
 kubectl logs -f deployment/awx -n awx -c awx-web
```

To tail logs from the web containers
```bash
 kubectl logs -f deployment/awx -n awx -c awx-web
```

NOTE: If there's multiple replica of the awx deployment you can use `stern` to tail logs from all replicas. For more information about `stern` check out https://github.com/wercker/stern.

To exec in to the a instance of the awx-task container:
```bash
 kubectl exec -it deployment/awx -n awx -c awx-task bash
```

The application will live reload when files are edited just like in the development environment. Just like in the development environment, if the application totally crashes because files are invalid syntax or other fatal problem, you will get an error like "no python application" in the web container. Delete the whole control plane pod and wait until a new one spins up automatically.
```bash
oc delete pod -l app.kubernetes.io/component=awx
```
