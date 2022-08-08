# Running Development Environment in Kubernetes using Kind Cluster

## Start Kind Cluster
Note: This environment has only been tested on MacOS with Docker.

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
```
$ kind create cluster --config kind-cluster.yaml
```

Verify AWX source tree is mounted in the kind-control-plane container
```
$ docker exec -it kind-control-plane ls /awx_devel
```

## Deploy the AWX Operator

Clone the [awx-operator](https://github.com/ansible/awx-operator).

For the following playbooks to work, you will need to:

```
$ pip install openshift
```

If you are not changing any code in the operator itself, git checkout the latest version from https://github.com/ansible/awx-operator/releases, and then follow the instructions in the awx-operator [README](https://github.com/ansible/awx-operator#basic-install).

If making changes to the operator itself, run the following command in the root
of the awx-operator repo. If not, continue to the next section.

### Building and Deploying a Custom AWX Operator Image

```
# in awx-operator repo on the branch you want to use
$ export IMAGE_TAG_BASE=quay.io/<username>/awx-operator
$ make docker-build docker-push deploy
```

Check the operator deployment
```
$ kubectl get deployments
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
awx-operator-controller-manager   1/1     1            1           16h
```

## Deploy AWX into Kind Cluster using the AWX Operator

If have have not made any changes to the AWX Dockerfile, run the following
command. If you need to test out changes to the Dockerfile, see the
"Custom AWX Development Image for Kubernetes" section below.

In the root of awx-operator:

```
$ ansible-playbook ansible/instantiate-awx-deployment.yml \
    -e development_mode=yes \
    -e image=ghcr.io/ansible/awx_kube_devel \
    -e image_version=devel \
    -e image_pull_policy=Always \
    -e service_type=nodeport \
    -e namespace=awx
```
Check the operator with the following commands:

```
# Check the operator deployment
$ kubectl get deployments
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
awx                               1/1     1            1           16h
awx-operator-controller-manager   1/1     1            1           16h

$ kubectl get pods
NAME                                              READY   STATUS    RESTARTS   AGE
awx-operator-controller-manager-b775bfc7c-fn995   2/2     Running   0          16h
```

If there are errors in the image pull, check that it is using the right tag. You can update the tag that it will pull by editing the deployment.

### Custom AWX Development Image for Kubernetes

In the root of the AWX repo:

```
$ make awx-kube-dev-build
$ docker push ghcr.io/ansible/awx_kube_devel:${COMPOSE_TAG}
```

In the root of awx-operator:

```
$ ansible-playbook ansible/instantiate-awx-deployment.yml \
    -e development_mode=yes \
    -e image=ghcr.io/ansible/awx_kube_devel \
    -e image_version=${COMPOSE_TAG} \
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
```
$ kubectl get secrets awx-admin-password -o json | jq '.data.password' | xargs | base64 -d
```

To tail logs from the task containers
```
$ kubectl logs -f deployment/awx -n awx -c awx-web
```

To tail logs from the web containers
```
$ kubectl logs -f deployment/awx -n awx -c awx-web
```

NOTE: If there's multiple replica of the awx deployment you can use `stern` to tail logs from all replicas. For more information about `stern` check out https://github.com/wercker/stern.

To exec in to the a instance of the awx-task container:
```
$ kubectl exec -it deployment/awx -c awx-task bash
```

The application will live reload when files are edited just like in the development environment. Just like in the development environment, if the application totally crashes because files are invalid syntax or other fatal problem, you will get an error like "no python application" in the web container. Delete the whole control plane pod and wait until a new one spins up automatically.
```
oc delete pod -l app.kubernetes.io/component=awx
```
