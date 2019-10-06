import os
import stat
import time
import yaml
import tempfile
import logging
from base64 import b64encode

from django.conf import settings
from kubernetes import client, config
from django.utils.functional import cached_property

from awx.main.utils.common import parse_yaml_or_json

logger = logging.getLogger('awx.main.scheduler')


class PodManager(object):

    def __init__(self, task=None):
        self.task = task

    def deploy(self):
        if not self.credential.kubernetes:
            raise RuntimeError('Pod deployment cannot occur without a Kubernetes credential')

        self.kube_api.create_namespaced_pod(body=self.pod_definition,
                                            namespace=self.namespace,
                                            _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT)

        num_retries = settings.AWX_CONTAINER_GROUP_POD_LAUNCH_RETRIES
        for retry_attempt in range(num_retries - 1):
            logger.debug(f"Checking for pod {self.pod_name}. Attempt {retry_attempt + 1} of {num_retries}")
            pod = self.kube_api.read_namespaced_pod(name=self.pod_name,
                                                    namespace=self.namespace,
                                                    _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT)
            if pod.status.phase != 'Pending':
                break
            else:
                logger.debug(f"Pod {self.pod_name} is Pending.")
                time.sleep(settings.AWX_CONTAINER_GROUP_POD_LAUNCH_RETRY_DELAY)
                continue

        if pod.status.phase == 'Running':
            logger.debug(f"Pod {self.pod_name} is online.")
            return pod
        else:
            logger.warn(f"Pod {self.pod_name} did not start. Status is {pod.status.phase}.")

    def delete(self):
        return self.kube_api.delete_namespaced_pod(name=self.pod_name,
                                                   namespace=self.namespace,
                                                   _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT)

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
        my_client = config.new_client_from_config(config_file=self.kube_config)
        return client.CoreV1Api(api_client=my_client)

    @property
    def pod_name(self):
        return f"job-{self.task.id}"

    @property
    def pod_definition(self):
        default_pod_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "namespace": settings.AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE
            },
            "spec": {
                "containers": [{
                    "image": settings.AWX_CONTAINER_GROUP_DEFAULT_IMAGE,
                    "tty": True,
                    "stdin": True,
                    "imagePullPolicy": "Always",
                    "args": [
                        'sleep', 'infinity'
                    ]
                }]
            }
        }

        pod_spec_override = {}
        if self.task and self.task.instance_group.pod_spec_override:
            pod_spec_override = parse_yaml_or_json(
                self.task.instance_group.pod_spec_override)
        pod_spec = {**default_pod_spec, **pod_spec_override}

        if self.task:
            pod_spec['metadata']['name'] = self.pod_name
            pod_spec['spec']['containers'][0]['name'] = self.pod_name

        return pod_spec


def generate_tmp_kube_config(credential, namespace):
    host_input = credential.get_input('host')
    config = {
        "apiVersion": "v1",
        "kind": "Config",
        "preferences": {},
        "clusters": [
            {
                "name": host_input,
                "cluster": {
                    "server": host_input
                }
            }
        ],
        "users": [
            {
                "name": host_input,
                "user": {
                    "token": credential.get_input('bearer_token')
                }
            }
        ],
        "contexts": [
            {
                "name": host_input,
                "context": {
                    "cluster": host_input,
                    "user": host_input,
                    "namespace": namespace
                }
            }
        ],
        "current-context": host_input
    }

    if credential.get_input('verify_ssl'):
        config["clusters"][0]["cluster"]["certificate-authority-data"] = b64encode(
            credential.get_input('ssl_ca_cert').encode() # encode to bytes
        ).decode() # decode the base64 data into a str
    else:
        config["clusters"][0]["cluster"]["insecure-skip-tls-verify"] = True

    fd, path = tempfile.mkstemp(prefix='kubeconfig')
    with open(path, 'wb') as temp:
        temp.write(yaml.dump(config).encode())
        temp.flush()
        os.chmod(temp.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return path
