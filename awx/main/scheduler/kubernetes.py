import collections
import json
import logging
from base64 import b64encode
from urllib import parse as urlparse

from django.conf import settings
from kubernetes import client, config
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from awx.main.utils.common import parse_yaml_or_json, deepmerge
from awx.main.utils.execution_environments import get_default_pod_spec

logger = logging.getLogger('awx.main.scheduler')


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

    def create_secret(self, job):
        registry_cred = job.execution_environment.credential
        host = registry_cred.get_input('host')
        # urlparse requires '//' to be provided if scheme is not specified
        original_parsed = urlparse.urlsplit(host)
        if (not original_parsed.scheme and not host.startswith('//')) or original_parsed.hostname is None:
            host = 'https://%s' % (host)
        parsed = urlparse.urlsplit(host)
        host = parsed.hostname
        if parsed.port:
            host = "{0}:{1}".format(host, parsed.port)

        username = registry_cred.get_input("username")
        password = registry_cred.get_input("password")

        # Construct container auth dict and base64 encode it
        token = b64encode("{}:{}".format(username, password).encode('UTF-8')).decode()
        auth_dict = json.dumps({"auths": {host: {"auth": token}}}, indent=4)
        auth_data = b64encode(str(auth_dict).encode('UTF-8')).decode()

        # Construct Secret object
        secret = client.V1Secret()
        secret_name = "automation-{0}-image-pull-secret-{1}".format(settings.INSTALL_UUID[:5], job.execution_environment.credential.id)
        secret.metadata = client.V1ObjectMeta(name="{}".format(secret_name))
        secret.type = "kubernetes.io/dockerconfigjson"
        secret.kind = "Secret"
        secret.data = {".dockerconfigjson": auth_data}

        # Check if secret already exists
        replace_secret = False
        try:
            existing_secret = self.kube_api.read_namespaced_secret(namespace=self.namespace, name=secret_name)
            if existing_secret.data != secret.data:
                replace_secret = True
            secret_exists = True
        except client.rest.ApiException as e:
            if e.status == 404:
                secret_exists = False
            else:
                error_msg = _('Invalid openshift or k8s cluster credential')
                if e.status == 403:
                    error_msg = _(
                        'Failed to create secret for container group {} because additional service account role rules are needed.  Add get, create and delete role rules for secret resources for your cluster credential.'.format(
                            job.instance_group.name
                        )
                    )
                full_error_msg = '{0}: {1}'.format(error_msg, str(e))
                logger.exception(full_error_msg)
                raise PermissionError(full_error_msg)

        if replace_secret:
            try:
                # Try to replace existing secret
                self.kube_api.delete_namespaced_secret(name=secret.metadata.name, namespace=self.namespace)
                self.kube_api.create_namespaced_secret(namespace=self.namespace, body=secret)
            except client.rest.ApiException as e:
                error_msg = _('Invalid openshift or k8s cluster credential')
                if e.status == 403:
                    error_msg = _(
                        'Failed to delete secret for container group {} because additional service account role rules are needed.  Add create and delete role rules for secret resources for your cluster credential.'.format(
                            job.instance_group.name
                        )
                    )
                full_error_msg = '{0}: {1}'.format(error_msg, str(e))
                logger.exception(full_error_msg)
                # let job continue for the case where secret was created manually and cluster cred doesn't have permission to create a secret
            except Exception as e:
                error_msg = 'Failed to create imagePullSecret for container group {}'.format(job.instance_group.name)
                logger.exception('{0}: {1}'.format(error_msg, str(e)))
                raise RuntimeError(error_msg)
        elif secret_exists and not replace_secret:
            pass
        else:
            # Create an image pull secret in namespace
            try:
                self.kube_api.create_namespaced_secret(namespace=self.namespace, body=secret)
            except client.rest.ApiException as e:
                if e.status == 403:
                    error_msg = _(
                        'Failed to create imagePullSecret: {}. Check that openshift or k8s credential has permission to create a secret.'.format(e.status)
                    )
                    logger.exception(error_msg)
                    # let job continue for the case where secret was created manually and cluster cred doesn't have permission to create a secret
            except Exception:
                error_msg = 'Failed to create imagePullSecret for container group {}'.format(job.instance_group.name)
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
        pod_spec = deepmerge(default_pod_spec, pod_spec_override)

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
