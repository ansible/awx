import collections
import json
import logging
from base64 import b64encode

from django.conf import settings
from kubernetes import client, config
from django.utils.functional import cached_property

from awx.main.utils.common import parse_yaml_or_json
from awx.main.utils.execution_environments import get_default_pod_spec

logger = logging.getLogger('awx.main.scheduler')


def deepmerge(a, b):
    """
    Merge dict structures and return the result.

    >>> a = {'first': {'all_rows': {'pass': 'dog', 'number': '1'}}}
    >>> b = {'first': {'all_rows': {'fail': 'cat', 'number': '5'}}}
    >>> import pprint; pprint.pprint(deepmerge(a, b))
    {'first': {'all_rows': {'fail': 'cat', 'number': '5', 'pass': 'dog'}}}
    """
    if isinstance(a, dict) and isinstance(b, dict):
        return dict([(k, deepmerge(a.get(k), b.get(k))) for k in set(a.keys()).union(b.keys())])
    elif b is None:
        return a
    else:
        return b


class PodManager(object):
    def __init__(self, task=None):
        self.task = task

    @classmethod
    def list_active_jobs(self, instance_group):
        task = collections.namedtuple('Task', 'id instance_group')(id='', instance_group=instance_group)
        pm = PodManager(task)
        pods = {}
        try:
            for pod in pm.kube_api.list_namespaced_pod(pm.namespace, label_selector='ansible-awx={}'.format(settings.INSTALL_UUID)).to_dict().get('items', []):
                job = pod['metadata'].get('labels', {}).get('ansible-awx-job-id')
                if job:
                    try:
                        pods[int(job)] = pod['metadata']['name']
                    except ValueError:
                        pass
        except Exception:
            logger.exception('Failed to list pods for container group {}'.format(instance_group))

        return pods

    @classmethod
    def create_secret(self, job):
        task = collections.namedtuple('Task', 'id instance_group')(id='', instance_group=job.instance_group)
        pm = PodManager(task)
        registry_cred = job.execution_environment.credential
        host = registry_cred.get_input('host').split('/')[0]
        username = registry_cred.get_input("username")
        password = registry_cred.get_input("password")

        # Construct container auth dict and base64 encode it
        token = b64encode("{}:{}".format(username, password).encode('ascii')).decode()
        auth_dict = json.dumps({"auths": {host: {"auth": token}}}, indent=4)
        auth_data = b64encode(str(auth_dict).encode('ascii')).decode()

        # Construct Secret object
        secret = client.V1Secret()
        secret_name = "automation-{0}-image-pull-secret-{1}".format(settings.INSTALL_UUID[:5], job.execution_environment.credential.id)
        secret.metadata = client.V1ObjectMeta(name="{}".format(secret_name))
        secret.type = "kubernetes.io/dockerconfigjson"
        secret.kind = "Secret"
        secret.data = {".dockerconfigjson": auth_data}

        # Check if secret already exists
        secrets = None
        try:
            secrets = pm.kube_api.list_namespaced_secret(namespace=pm.namespace)
        except client.rest.ApiException:
            error_msg = 'Invalid openshift or k8s cluster credential'
            logger.exception(error_msg)
            job.cancel(job_explanation=error_msg)
            raise

        if secrets:
            secret_exists = False
            secrets_dict = secrets.to_dict().get('items', [])
            for s in secrets_dict:
                if s['metadata']['name'] == secret_name:
                    secret_exists = True
            if secret_exists:
                try:
                    # Try to replace existing secret
                    pm.kube_api.delete_namespaced_secret(name=secret.metadata.name, namespace=pm.namespace)
                    pm.kube_api.create_namespaced_secret(namespace=pm.namespace, body=secret)
                except Exception:
                    error_msg = 'Failed to create imagePullSecret for container group {}'.format(task.instance_group.name)
                    logger.exception(error_msg)
                    job.cancel(job_explanation=error_msg)
                    raise
            else:
                # Create an image pull secret in namespace
                try:
                    pm.kube_api.create_namespaced_secret(namespace=pm.namespace, body=secret)
                except client.rest.ApiException as e:
                    if e.status == 401:
                        error_msg = 'Failed to create imagePullSecret: {}. Check that openshift or k8s credential has permission to create a secret.'.format(
                            e.status
                        )
                        logger.exception(error_msg)
                        # let job run for the case that the secret exists but the cluster cred doesn't have permission to create a secret
                except Exception:
                    error_msg = 'Failed to create imagePullSecret for container group {}'.format(task.instance_group.name)
                    logger.exception(error_msg)
                    job.cancel(job_explanation=error_msg)

        return secret.metadata.name

    @property
    def namespace(self):
        return self.pod_definition['metadata']['namespace']

    @property
    def credential(self):
        return self.task.instance_group.credential

    @cached_property
    def kube_config(self):
        return generate_tmp_kube_config(self.credential, self.namespace)

    @cached_property
    def kube_api(self):
        # this feels a little janky, but it's what k8s' own code does
        # internally when it reads kube config files from disk:
        # https://github.com/kubernetes-client/python-base/blob/0b208334ef0247aad9afcaae8003954423b61a0d/config/kube_config.py#L643
        if self.credential:
            loader = config.kube_config.KubeConfigLoader(config_dict=self.kube_config)
            cfg = type.__call__(client.Configuration)
            loader.load_and_set(cfg)
            api = client.CoreV1Api(api_client=client.ApiClient(configuration=cfg))
        else:
            config.load_incluster_config()
            api = client.CoreV1Api()

        return api

    @property
    def pod_name(self):
        return f"automation-job-{self.task.id}"

    @property
    def pod_definition(self):
        default_pod_spec = get_default_pod_spec()

        pod_spec_override = {}
        if self.task and self.task.instance_group.pod_spec_override:
            pod_spec_override = parse_yaml_or_json(self.task.instance_group.pod_spec_override)
        pod_spec = {**default_pod_spec, **pod_spec_override}

        if self.task:
            pod_spec['metadata'] = deepmerge(
                pod_spec.get('metadata', {}), dict(name=self.pod_name, labels={'ansible-awx': settings.INSTALL_UUID, 'ansible-awx-job-id': str(self.task.id)})
            )
            pod_spec['spec']['containers'][0]['name'] = self.pod_name

        return pod_spec


def generate_tmp_kube_config(credential, namespace):
    host_input = credential.get_input('host')
    config = {
        "apiVersion": "v1",
        "kind": "Config",
        "preferences": {},
        "clusters": [{"name": host_input, "cluster": {"server": host_input}}],
        "users": [{"name": host_input, "user": {"token": credential.get_input('bearer_token')}}],
        "contexts": [{"name": host_input, "context": {"cluster": host_input, "user": host_input, "namespace": namespace}}],
        "current-context": host_input,
    }

    if credential.get_input('verify_ssl') and 'ssl_ca_cert' in credential.inputs:
        config["clusters"][0]["cluster"]["certificate-authority-data"] = b64encode(
            credential.get_input('ssl_ca_cert').encode()  # encode to bytes
        ).decode()  # decode the base64 data into a str
    else:
        config["clusters"][0]["cluster"]["insecure-skip-tls-verify"] = True
    return config
