# Python
from base64 import b64encode
from collections import namedtuple
import concurrent.futures
from enum import Enum
import logging
import os
import shutil
import socket
import time
import yaml

# Django
from django.conf import settings
from django.db import connections

# Runner
import ansible_runner

# AWX
from awx.main.utils.execution_environments import get_default_pod_spec
from awx.main.exceptions import ReceptorNodeNotFound
from awx.main.utils.common import (
    deepmerge,
    parse_yaml_or_json,
    cleanup_new_process,
)
from awx.main.constants import MAX_ISOLATED_PATH_COLON_DELIMITER
from awx.main.tasks.signals import signal_state, signal_callback, SignalExit
from awx.main.models import Instance
from awx.main.dispatch.publish import task

# Receptorctl
from receptorctl.socket_interface import ReceptorControl

from filelock import FileLock

logger = logging.getLogger('awx.main.tasks.receptor')
__RECEPTOR_CONF = '/etc/receptor/receptor.conf'
__RECEPTOR_CONF_LOCKFILE = f'{__RECEPTOR_CONF}.lock'
RECEPTOR_ACTIVE_STATES = ('Pending', 'Running')


class ReceptorConnectionType(Enum):
    DATAGRAM = 0
    STREAM = 1
    STREAMTLS = 2


def get_receptor_sockfile():
    lock = FileLock(__RECEPTOR_CONF_LOCKFILE)
    with lock:
        with open(__RECEPTOR_CONF, 'r') as f:
            data = yaml.safe_load(f)
    for section in data:
        for entry_name, entry_data in section.items():
            if entry_name == 'control-service':
                if 'filename' in entry_data:
                    return entry_data['filename']
                else:
                    raise RuntimeError(f'Receptor conf {__RECEPTOR_CONF} control-service entry does not have a filename parameter')
    else:
        raise RuntimeError(f'Receptor conf {__RECEPTOR_CONF} does not have control-service entry needed to get sockfile')


def get_tls_client(use_stream_tls=None):
    if not use_stream_tls:
        return None

    lock = FileLock(__RECEPTOR_CONF_LOCKFILE)
    with lock:
        with open(__RECEPTOR_CONF, 'r') as f:
            data = yaml.safe_load(f)
    for section in data:
        for entry_name, entry_data in section.items():
            if entry_name == 'tls-client':
                if 'name' in entry_data:
                    return entry_data['name']
    return None


def get_receptor_ctl():
    receptor_sockfile = get_receptor_sockfile()
    try:
        return ReceptorControl(receptor_sockfile, config=__RECEPTOR_CONF, tlsclient=get_tls_client(True))
    except RuntimeError:
        return ReceptorControl(receptor_sockfile)


def find_node_in_mesh(node_name, receptor_ctl):
    attempts = 10
    backoff = 1
    for attempt in range(attempts):
        all_nodes = receptor_ctl.simple_command("status").get('Advertisements', None)
        for node in all_nodes:
            if node.get('NodeID') == node_name:
                return node
        else:
            logger.warning(f"Instance {node_name} is not in the receptor mesh. {attempts-attempt} attempts left.")
            time.sleep(backoff)
            backoff += 1
    else:
        raise ReceptorNodeNotFound(f'Instance {node_name} is not in the receptor mesh')


def get_conn_type(node_name, receptor_ctl):
    node = find_node_in_mesh(node_name, receptor_ctl)
    return ReceptorConnectionType(node.get('ConnType'))


def administrative_workunit_reaper(work_list=None):
    """
    This releases completed work units that were spawned by actions inside of this module
    specifically, this should catch any completed work unit left by
     - worker_info
     - worker_cleanup
    These should ordinarily be released when the method finishes, but this is a
    cleanup of last-resort, in case something went awry
    """
    receptor_ctl = get_receptor_ctl()
    if work_list is None:
        work_list = receptor_ctl.simple_command("work list")

    for unit_id, work_data in work_list.items():
        extra_data = work_data.get('ExtraData')
        if extra_data is None:
            continue  # if this is not ansible-runner work, we do not want to touch it
        if isinstance(extra_data, str):
            if not work_data.get('StateName', None) or work_data.get('StateName') in RECEPTOR_ACTIVE_STATES:
                continue
        else:
            if extra_data.get('RemoteWorkType') != 'ansible-runner':
                continue
            params = extra_data.get('RemoteParams', {}).get('params')
            if not params:
                continue
            if not (params == '--worker-info' or params.startswith('cleanup')):
                continue  # if this is not a cleanup or health check, we do not want to touch it
            if work_data.get('StateName') in RECEPTOR_ACTIVE_STATES:
                continue  # do not want to touch active work units
            logger.info(f'Reaping orphaned work unit {unit_id} with params {params}')
        receptor_ctl.simple_command(f"work release {unit_id}")


class RemoteJobError(RuntimeError):
    pass


def run_until_complete(node, timing_data=None, **kwargs):
    """
    Runs an ansible-runner work_type on remote node, waits until it completes, then returns stdout.
    """
    receptor_ctl = get_receptor_ctl()

    use_stream_tls = getattr(get_conn_type(node, receptor_ctl), 'name', None) == "STREAMTLS"
    kwargs.setdefault('tlsclient', get_tls_client(use_stream_tls))
    kwargs.setdefault('ttl', '20s')
    kwargs.setdefault('payload', '')

    transmit_start = time.time()
    sign_work = False if settings.IS_K8S else True
    result = receptor_ctl.submit_work(worktype='ansible-runner', node=node, signwork=sign_work, **kwargs)

    unit_id = result['unitid']
    run_start = time.time()
    if timing_data:
        timing_data['transmit_timing'] = run_start - transmit_start
    run_timing = 0.0
    stdout = ''

    try:

        resultfile = receptor_ctl.get_work_results(unit_id)

        while run_timing < 20.0:
            status = receptor_ctl.simple_command(f'work status {unit_id}')
            state_name = status.get('StateName')
            if state_name not in RECEPTOR_ACTIVE_STATES:
                break
            run_timing = time.time() - run_start
            time.sleep(0.5)
        else:
            raise RemoteJobError(f'Receptor job timeout on {node} after {run_timing} seconds, state remains in {state_name}')

        if timing_data:
            timing_data['run_timing'] = run_timing

        stdout = resultfile.read()
        stdout = str(stdout, encoding='utf-8')

    finally:

        if settings.RECEPTOR_RELEASE_WORK:
            res = receptor_ctl.simple_command(f"work release {unit_id}")
            if res != {'released': unit_id}:
                logger.warning(f'Could not confirm release of receptor work unit id {unit_id} from {node}, data: {res}')

        receptor_ctl.close()

    if state_name.lower() == 'failed':
        work_detail = status.get('Detail', '')
        if work_detail:
            raise RemoteJobError(f'Receptor error from {node}, detail:\n{work_detail}')
        else:
            raise RemoteJobError(f'Unknown ansible-runner error on node {node}, stdout:\n{stdout}')

    return stdout


def worker_info(node_name, work_type='ansible-runner'):
    error_list = []
    data = {'errors': error_list, 'transmit_timing': 0.0}

    try:
        stdout = run_until_complete(node=node_name, timing_data=data, params={"params": "--worker-info"})

        yaml_stdout = stdout.strip()
        remote_data = {}
        try:
            remote_data = yaml.safe_load(yaml_stdout)
        except Exception as json_e:
            error_list.append(f'Failed to parse node {node_name} --worker-info output as YAML, error: {json_e}, data:\n{yaml_stdout}')

        if not isinstance(remote_data, dict):
            error_list.append(f'Remote node {node_name} --worker-info output is not a YAML dict, output:{stdout}')
        else:
            error_list.extend(remote_data.pop('errors', []))  # merge both error lists
            data.update(remote_data)

    except RemoteJobError as exc:
        details = exc.args[0]
        if 'unrecognized arguments: --worker-info' in details:
            error_list.append(f'Old version (2.0.1 or earlier) of ansible-runner on node {node_name} without --worker-info')
        else:
            error_list.append(details)

    except (ReceptorNodeNotFound, RuntimeError) as exc:
        error_list.append(str(exc))

    # If we have a connection error, missing keys would be trivial consequence of that
    if not data['errors']:
        # see tasks.py usage of keys
        missing_keys = set(('runner_version', 'mem_in_bytes', 'cpu_count')) - set(data.keys())
        if missing_keys:
            data['errors'].append('Worker failed to return keys {}'.format(' '.join(missing_keys)))

    return data


def _convert_args_to_cli(vargs):
    """
    For the ansible-runner worker cleanup command
    converts the dictionary (parsed argparse variables) used for python interface
    into a string of CLI options, which has to be used on execution nodes.
    """
    args = ['cleanup']
    for option in ('exclude_strings', 'remove_images'):
        if vargs.get(option):
            args.append('--{}={}'.format(option.replace('_', '-'), ' '.join(vargs.get(option))))
    for option in ('file_pattern', 'image_prune', 'process_isolation_executable', 'grace_period'):
        if vargs.get(option) is True:
            args.append('--{}'.format(option.replace('_', '-')))
        elif vargs.get(option) not in (None, ''):
            args.append('--{}={}'.format(option.replace('_', '-'), vargs.get(option)))
    return args


def worker_cleanup(node_name, vargs, timeout=300.0):
    args = _convert_args_to_cli(vargs)

    remote_command = ' '.join(args)
    logger.debug(f'Running command over receptor mesh on {node_name}: ansible-runner worker {remote_command}')

    stdout = run_until_complete(node=node_name, params={"params": remote_command})

    return stdout


class AWXReceptorJob:
    def __init__(self, task, runner_params=None):
        self.task = task
        self.runner_params = runner_params
        self.unit_id = None

        if self.task and not self.task.instance.is_container_group_task:
            execution_environment_params = self.task.build_execution_environment_params(self.task.instance, runner_params['private_data_dir'])
            self.runner_params.update(execution_environment_params)

        if not settings.IS_K8S and self.work_type == 'local' and 'only_transmit_kwargs' not in self.runner_params:
            self.runner_params['only_transmit_kwargs'] = True

    def run(self):
        # We establish a connection to the Receptor socket
        receptor_ctl = get_receptor_ctl()

        res = None
        try:
            res = self._run_internal(receptor_ctl)
            return res
        finally:
            # Make sure to always release the work unit if we established it
            if self.unit_id is not None and settings.RECEPTOR_RELEASE_WORK:
                try:
                    receptor_ctl.simple_command(f"work release {self.unit_id}")
                except Exception:
                    logger.exception(f"Error releasing work unit {self.unit_id}.")

    @property
    def sign_work(self):
        return False if settings.IS_K8S else True

    def _run_internal(self, receptor_ctl):
        # Create a socketpair. Where the left side will be used for writing our payload
        # (private data dir, kwargs). The right side will be passed to Receptor for
        # reading.
        sockin, sockout = socket.socketpair()

        # Prepare the submit_work kwargs before creating threads, because references to settings are not thread-safe
        work_submit_kw = dict(worktype=self.work_type, params=self.receptor_params, signwork=self.sign_work)
        if self.work_type == 'ansible-runner':
            work_submit_kw['node'] = self.task.instance.execution_node
            use_stream_tls = get_conn_type(work_submit_kw['node'], receptor_ctl).name == "STREAMTLS"
            work_submit_kw['tlsclient'] = get_tls_client(use_stream_tls)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            transmitter_future = executor.submit(self.transmit, sockin)

            # submit our work, passing in the right side of our socketpair for reading.
            result = receptor_ctl.submit_work(payload=sockout.makefile('rb'), **work_submit_kw)

            sockin.close()
            sockout.close()

            self.unit_id = result['unitid']
            # Update the job with the work unit in-memory so that the log_lifecycle
            # will print out the work unit that is to be associated with the job in the database
            # via the update_model() call.
            # We want to log the work_unit_id as early as possible. A failure can happen in between
            # when we start the job in receptor and when we associate the job <-> work_unit_id.
            # In that case, there will be work running in receptor and Controller will not know
            # which Job it is associated with.
            # We do not programatically handle this case. Ideally, we would handle this with a reaper case.
            # The two distinct job lifecycle log events below allow for us to at least detect when this
            # edge case occurs. If the lifecycle event work_unit_id_received occurs without the
            # work_unit_id_assigned event then this case may have occured.
            self.task.instance.work_unit_id = result['unitid']  # Set work_unit_id in-memory only
            self.task.instance.log_lifecycle("work_unit_id_received")
            self.task.update_model(self.task.instance.pk, work_unit_id=result['unitid'])
            self.task.instance.log_lifecycle("work_unit_id_assigned")

        # Throws an exception if the transmit failed.
        # Will be caught by the try/except in BaseTask#run.
        transmitter_future.result()

        # Artifacts are an output, but sometimes they are an input as well
        # this is the case with fact cache, where clearing facts deletes a file, and this must be captured
        artifact_dir = os.path.join(self.runner_params['private_data_dir'], 'artifacts')
        if self.work_type != 'local' and os.path.exists(artifact_dir):
            shutil.rmtree(artifact_dir)

        resultsock, resultfile = receptor_ctl.get_work_results(self.unit_id, return_socket=True, return_sockfile=True)

        connections.close_all()

        # "processor" and the main thread will be separate threads.
        # If a cancel happens, the main thread will encounter an exception, in which case
        # we yank the socket out from underneath the processor, which will cause it to exit.
        # The ThreadPoolExecutor context manager ensures we do not leave any threads laying around.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            processor_future = executor.submit(self.processor, resultfile)

            try:
                signal_state.raise_exception = True
                # address race condition where SIGTERM was issued after this dispatcher task started
                if signal_callback():
                    raise SignalExit()
                res = processor_future.result()
            except SignalExit:
                receptor_ctl.simple_command(f"work cancel {self.unit_id}")
                resultsock.shutdown(socket.SHUT_RDWR)
                resultfile.close()
                result = namedtuple('result', ['status', 'rc'])
                res = result('canceled', 1)
            finally:
                signal_state.raise_exception = False

            if res.status == 'error':
                # If ansible-runner ran, but an error occured at runtime, the traceback information
                # is saved via the status_handler passed in to the processor.
                if 'result_traceback' in self.task.runner_callback.extra_update_fields:
                    return res

                try:
                    unit_status = receptor_ctl.simple_command(f'work status {self.unit_id}')
                    detail = unit_status.get('Detail', None)
                    state_name = unit_status.get('StateName', None)
                except Exception:
                    detail = ''
                    state_name = ''
                    logger.exception(f'An error was encountered while getting status for work unit {self.unit_id}')

                if 'exceeded quota' in detail:
                    logger.warning(detail)
                    log_name = self.task.instance.log_format
                    logger.warning(f"Could not launch pod for {log_name}. Exceeded quota.")
                    self.task.update_model(self.task.instance.pk, status='pending')
                    return

                try:
                    resultsock = receptor_ctl.get_work_results(self.unit_id, return_sockfile=True)
                    lines = resultsock.readlines()
                    receptor_output = b"".join(lines).decode()
                    if receptor_output:
                        self.task.runner_callback.delay_update(result_traceback=receptor_output)
                    elif detail:
                        self.task.runner_callback.delay_update(result_traceback=detail)
                    else:
                        logger.warning(f'No result details or output from {self.task.instance.log_format}, status:\n{state_name}')
                except Exception:
                    raise RuntimeError(detail)

        return res

    # Spawned in a thread so Receptor can start reading before we finish writing, we
    # write our payload to the left side of our socketpair.
    @cleanup_new_process
    def transmit(self, _socket):
        try:
            ansible_runner.interface.run(streamer='transmit', _output=_socket.makefile('wb'), **self.runner_params)
        finally:
            # Socket must be shutdown here, or the reader will hang forever.
            _socket.shutdown(socket.SHUT_WR)

    @cleanup_new_process
    def processor(self, resultfile):
        return ansible_runner.interface.run(
            streamer='process',
            quiet=True,
            _input=resultfile,
            event_handler=self.task.runner_callback.event_handler,
            finished_callback=self.task.runner_callback.finished_callback,
            status_handler=self.task.runner_callback.status_handler,
            **self.runner_params,
        )

    @property
    def receptor_params(self):
        if self.task.instance.is_container_group_task:
            spec_yaml = yaml.dump(self.pod_definition, explicit_start=True)

            receptor_params = {
                "secret_kube_pod": spec_yaml,
                "pod_pending_timeout": getattr(settings, 'AWX_CONTAINER_GROUP_POD_PENDING_TIMEOUT', "5m"),
            }

            if self.credential:
                kubeconfig_yaml = yaml.dump(self.kube_config, explicit_start=True)
                receptor_params["secret_kube_config"] = kubeconfig_yaml
        else:
            private_data_dir = self.runner_params['private_data_dir']
            if self.work_type == 'ansible-runner' and settings.AWX_CLEANUP_PATHS:
                # on execution nodes, we rely on the private data dir being deleted
                cli_params = f"--private-data-dir={private_data_dir} --delete"
            else:
                # on hybrid nodes, we rely on the private data dir NOT being deleted
                cli_params = f"--private-data-dir={private_data_dir}"
            receptor_params = {"params": cli_params}

        return receptor_params

    @property
    def work_type(self):
        if self.task.instance.is_container_group_task:
            if self.credential:
                return 'kubernetes-runtime-auth'
            return 'kubernetes-incluster-auth'
        if self.task.instance.execution_node == settings.CLUSTER_HOST_ID or self.task.instance.execution_node == self.task.instance.controller_node:
            return 'local'
        return 'ansible-runner'

    @property
    def pod_definition(self):
        ee = self.task.instance.execution_environment

        default_pod_spec = get_default_pod_spec()

        pod_spec_override = {}
        if self.task and self.task.instance.instance_group.pod_spec_override:
            pod_spec_override = parse_yaml_or_json(self.task.instance.instance_group.pod_spec_override)
        # According to the deepmerge docstring, the second dictionary will override when
        # they share keys, which is the desired behavior.
        # This allows user to only provide elements they want to override, and for us to still provide any
        # defaults they don't want to change
        pod_spec = deepmerge(default_pod_spec, pod_spec_override)

        pod_spec['spec']['containers'][0]['image'] = ee.image
        pod_spec['spec']['containers'][0]['args'] = ['ansible-runner', 'worker', '--private-data-dir=/runner']

        # Enforce EE Pull Policy
        pull_options = {"always": "Always", "missing": "IfNotPresent", "never": "Never"}
        if self.task and self.task.instance.execution_environment:
            if self.task.instance.execution_environment.pull:
                pod_spec['spec']['containers'][0]['imagePullPolicy'] = pull_options[self.task.instance.execution_environment.pull]

        # This allows the user to also expose the isolated path list
        # to EEs running in k8s/ocp environments, i.e. container groups.
        # This assumes the node and SA supports hostPath volumes
        # type is not passed due to backward compatibility,
        # which means that no checks will be performed before mounting the hostPath volume.
        if settings.AWX_MOUNT_ISOLATED_PATHS_ON_K8S and settings.AWX_ISOLATION_SHOW_PATHS:
            spec_volume_mounts = []
            spec_volumes = []

            for idx, this_path in enumerate(settings.AWX_ISOLATION_SHOW_PATHS):
                mount_option = None
                if this_path.count(':') == MAX_ISOLATED_PATH_COLON_DELIMITER:
                    src, dest, mount_option = this_path.split(':')
                elif this_path.count(':') == MAX_ISOLATED_PATH_COLON_DELIMITER - 1:
                    src, dest = this_path.split(':')
                else:
                    src = dest = this_path

                # Enforce read-only volume if 'ro' has been explicitly passed
                # We do this so we can use the same configuration for regular scenarios and k8s
                # Since flags like ':O', ':z' or ':Z' are not valid in the k8s realm
                # Example: /data:/data:ro
                read_only = bool('ro' == mount_option)

                # Since type is not being passed, k8s by default will not perform any checks if the
                # hostPath volume exists on the k8s node itself.
                spec_volumes.append({'name': f'volume-{idx}', 'hostPath': {'path': src}})

                spec_volume_mounts.append({'name': f'volume-{idx}', 'mountPath': f'{dest}', 'readOnly': read_only})

            # merge any volumes definition already present in the pod_spec
            if 'volumes' in pod_spec['spec']:
                pod_spec['spec']['volumes'] += spec_volumes
            else:
                pod_spec['spec']['volumes'] = spec_volumes

            # merge any volumesMounts definition already present in the pod_spec
            if 'volumeMounts' in pod_spec['spec']['containers'][0]:
                pod_spec['spec']['containers'][0]['volumeMounts'] += spec_volume_mounts
            else:
                pod_spec['spec']['containers'][0]['volumeMounts'] = spec_volume_mounts

        if self.task and self.task.instance.is_container_group_task:
            # If EE credential is passed, create an imagePullSecret
            if self.task.instance.execution_environment and self.task.instance.execution_environment.credential:
                # Create pull secret in k8s cluster based on ee cred
                from awx.main.scheduler.kubernetes import PodManager  # prevent circular import

                pm = PodManager(self.task.instance)
                secret_name = pm.create_secret(job=self.task.instance)

                # Inject secret name into podspec
                pod_spec['spec']['imagePullSecrets'] = [{"name": secret_name}]

        if self.task:
            pod_spec['metadata'] = deepmerge(
                pod_spec.get('metadata', {}),
                dict(name=self.pod_name, labels={'ansible-awx': settings.INSTALL_UUID, 'ansible-awx-job-id': str(self.task.instance.id)}),
            )

        return pod_spec

    @property
    def pod_name(self):
        return f"automation-job-{self.task.instance.id}"

    @property
    def credential(self):
        return self.task.instance.instance_group.credential

    @property
    def namespace(self):
        return self.pod_definition['metadata']['namespace']

    @property
    def kube_config(self):
        host_input = self.credential.get_input('host')
        config = {
            "apiVersion": "v1",
            "kind": "Config",
            "preferences": {},
            "clusters": [{"name": host_input, "cluster": {"server": host_input}}],
            "users": [{"name": host_input, "user": {"token": self.credential.get_input('bearer_token')}}],
            "contexts": [{"name": host_input, "context": {"cluster": host_input, "user": host_input, "namespace": self.namespace}}],
            "current-context": host_input,
        }

        if self.credential.get_input('verify_ssl') and 'ssl_ca_cert' in self.credential.inputs:
            config["clusters"][0]["cluster"]["certificate-authority-data"] = b64encode(
                self.credential.get_input('ssl_ca_cert').encode()  # encode to bytes
            ).decode()  # decode the base64 data into a str
        else:
            config["clusters"][0]["cluster"]["insecure-skip-tls-verify"] = True
        return config


RECEPTOR_CONFIG_STARTER = (
    {'control-service': {'service': 'control', 'filename': '/var/run/receptor/receptor.sock', 'permissions': '0600'}},
    {'local-only': None},
    {'work-command': {'worktype': 'local', 'command': 'ansible-runner', 'params': 'worker', 'allowruntimeparams': True}},
    {
        'work-kubernetes': {
            'worktype': 'kubernetes-runtime-auth',
            'authmethod': 'runtime',
            'allowruntimeauth': True,
            'allowruntimepod': True,
            'allowruntimeparams': True,
        }
    },
    {
        'work-kubernetes': {
            'worktype': 'kubernetes-incluster-auth',
            'authmethod': 'incluster',
            'allowruntimeauth': True,
            'allowruntimepod': True,
            'allowruntimeparams': True,
        }
    },
    {
        'tls-client': {
            'name': 'tlsclient',
            'rootcas': '/etc/receptor/tls/ca/receptor-ca.crt',
            'cert': '/etc/receptor/tls/receptor.crt',
            'key': '/etc/receptor/tls/receptor.key',
        }
    },
)


@task()
def write_receptor_config():
    receptor_config = list(RECEPTOR_CONFIG_STARTER)

    instances = Instance.objects.exclude(node_type='control')
    for instance in instances:
        peer = {'tcp-peer': {'address': f'{instance.hostname}:{instance.listener_port}', 'tls': 'tlsclient'}}
        receptor_config.append(peer)

    lock = FileLock(__RECEPTOR_CONF_LOCKFILE)
    with lock:
        with open(__RECEPTOR_CONF, 'w') as file:
            yaml.dump(receptor_config, file, default_flow_style=False)

    receptor_ctl = get_receptor_ctl()

    attempts = 10
    backoff = 1
    for attempt in range(attempts):
        try:
            receptor_ctl.simple_command("reload")
            break
        except ValueError:
            logger.warning(f"Unable to reload Receptor configuration. {attempts-attempt} attempts left.")
            time.sleep(backoff)
            backoff += 1
    else:
        raise RuntimeError("Receptor reload failed")
