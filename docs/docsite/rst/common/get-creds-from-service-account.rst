
A ``ContainerGroup`` is a type of ``InstanceGroup`` that has an associated Credential that allows for connecting to an OpenShift cluster. To set up a container group, you must first have the following:

- A namespace you can launch into (every cluster has a “default” namespace, but you may want to use a specific namespace)
- A service account that has the roles that allow it to launch and manage Pods in this namespace
- If you will be using |ees| in a private registry, and have a Container Registry credential associated to them in AWX, the service account also needs the roles to get, create, and delete secrets in the namespace. If you do not want to give these roles to the service account, you can pre-create the ``ImagePullSecrets`` and specify them on the pod spec for the ContainerGroup. In this case, the |ee| should NOT have a Container Registry credential associated, or AWX will attempt to create the secret for you in the namespace.
- A token associated with that service account (OpenShift or Kubernetes Bearer Token)
- A CA certificate associated with the cluster

This section describes creating a Service Account in an Openshift cluster (or K8s) in order to be used to run jobs in a container group via AWX. After the Service Account is created, its credentials are provided to AWX in the form of an Openshift or Kubernetes API bearer token credential. Below describes how to create a service account and collect the needed information for configuring AWX. 

To configure AWX:

1. To create a service account, you may download and use this sample service account, :download:`containergroup sa <../common/containergroup-sa.yml>` and modify it as needed to obtain the above credentials.

2. Apply the configuration from ``containergroup-sa.yml``::

	oc apply -f containergroup-sa.yml


3. Get the secret name associated with the service account::

	export SA_SECRET=$(oc get sa containergroup-service-account -o json | jq '.secrets[0].name' | tr -d '"')

4. Get the token from the secret::

	oc get secret $(echo ${SA_SECRET}) -o json | jq '.data.token' | xargs | base64 --decode > containergroup-sa.token

5. Get the CA cert::

	oc get secret $SA_SECRET -o json | jq '.data["ca.crt"]' | xargs | base64 --decode > containergroup-ca.crt

6. Use the contents of ``containergroup-sa.token`` and ``containergroup-ca.crt`` to provide the information for the :ref:`ug_credentials_ocp_k8s` required for the container group.
