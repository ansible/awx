---
tags:
  - feature
---
# Container Groups

In a traditional AWX installation, jobs (ansible-playbook runs) are
executed directly on a member of the cluster.  The concept of a
Container Group (working name) allows for job environments to be
provisioned on-demand as a Pod that exists only for the duration of
the playbook run. This is known as the ephemeral execution model and
ensures a clean environment for every job run.

In some cases it is desirable to have the execution environment be "always-on",
this is is done by manually creating an instance through the AWX API or UI. 

## Configuration

A `ContainerGroup` is simply an `InstanceGroup` that has an associated Credential
that allows for connecting to an OpenShift or Kubernetes cluster.

### Kubernetes Service Account

```yaml
#
# Create service account / role / role-binding:
# oc -n my-namespace apply -f service-account.yml
#
# Obtain API token and CA cert:
#
# $ SECRET_NAME=$(oc -n my-namespace get sa awx -o json | jq -r '.secrets[0].name')
# $ oc -n my-namespace get secret $SECRET_NAME  -o json | jq -r '.data["token"]  | @base64d'
# $ oc -n my-namespace get secret $SECRET_NAME  -o json | jq -r '.data["ca.crt"] | @base64d'
#

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: awx

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-manager
rules:
  - apiGroups: [""]  # "" indicates the core API group
    resources: ["pods"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]

---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: awx-pod-manager
subjects:
  - kind: ServiceAccount
    name: awx
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-manager
```

To create a new type, add a new `ManagedCredentialType` to
`awx/main/models/credential/__init__.py` where `kind='kubernetes'`.

### Create Credential

A `Credential` must be created where the associated `CredentialType` is one of:

- `kubernetes_bearer_token`

Other credential types (such as username/password) may be added in the future.

### Create a Container Groupp

Once this `Credential` has been associated with an `InstanceGroup`, the
`InstanceGroup.kubernetes` property will return `True`.

#### Pod Customization

There will be a very simple default pod spec that lives in code.

A custom YAML document may be provided. This will allow the UI to implement
whatever fields necessary, because any custom fields (think 'image' or
'namespace') can be "serialized" as valid `Pod` JSON or YAML. A full list of
options can be found in the Kubernetes documentation
[here](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.15/#pod-v1-core).

```bash
cat > api_request.json <<EOF
{
  "apiVersion": "v1",
  "kind": "Pod",
  "metadata": {
    "namespace": "my-namespace"
  },
  "spec": {
    "containers": [
      {
        "args": [
          "sleep",
          "infinity"
        ],
        "image": "my-custom-image",
        "stdin": true,
        "tty": true
      }
    ]
  }
}
EOF

curl -Lk --user 'admin:password' \
     -X PATCH \
     -d @api_request.json \
     -H 'Content-Type: application/json' \
     https://localhost:8043/api/v2/instance_groups/2/
```
