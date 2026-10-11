# Python
from base64 import b64encode
from collections import namedtuple
import concurrent.futures
from datetime import datetime, timedelta, timezone
from enum import Enum
import io
import json
import logging
import os
import shutil
import socket
import tempfile
import time
import yaml

# Django
from django.conf import settings
from django.db import connections
from django.db.models import Exists, Max, OuterRef
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

# Runner
import ansible_runner

# django-ansible-base
from ansible_base.lib.utils.db import advisory_lock

# Dispatcherd
from dispatcherd.publish import task

# AWX
from awx.main.utils.execution_environments import get_default_pod_spec
from awx.main.utils.failpoints import failpoint
from awx.main.exceptions import ReceptorNodeNotFound
from awx.main.utils.common import (
    deepmerge,
    parse_yaml_or_json,
    cleanup_new_process,
)
from awx.main.constants import JOB_FOLDER_PREFIX, MAX_ISOLATED_PATH_COLON_DELIMITER
from awx.main.tasks.signals import signal_state, signal_callback, SignalExit
from awx.main.tasks.callback import RunnerCallback
from awx.main.tasks.adoption import invoke_adoption_hooks
from awx.main.models import Instance, InstanceLink, UnifiedJob, ReceptorAddress
from awx.main.dispatch import get_task_queuename


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


"""
Translate receptorctl messages that come in over stdout into
structured messages. Currently, these are error messages.
"""


class ReceptorErrorBase:
    _MESSAGE = 'Receptor Error'

    def __init__(self, node: str = 'N/A', state_name: str = 'N/A'):
        self.node = node
        self.state_name = state_name

    def __str__(self):
        return f"{self.__class__.__name__} '{self._MESSAGE}' on node '{self.node}' with state '{self.state_name}'"


class WorkUnitError(ReceptorErrorBase):
    _MESSAGE = 'unknown work unit '

    def __init__(self, work_unit_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.work_unit_id = work_unit_id

    def __str__(self):
        return f"{super().__str__()} work unit id '{self.work_unit_id}'"


class WorkUnitCancelError(WorkUnitError):
    _MESSAGE = 'error cancelling remote unit:  unknown work unit '


class WorkUnitResultsError(WorkUnitError):
    _MESSAGE = 'Failed to get results: unknown work unit '


class UnknownError(ReceptorErrorBase):
    _MESSAGE = 'Unknown receptor ctl error'

    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._MESSAGE = msg


class FuzzyError:
    def __new__(self, e: RuntimeError, node: str, state_name: str):
        """
        At the time of writing this comment all of the sub-classes detection
        is centralized in this parent class. It's like a Router().
        Someone may find it better to push down the error detection logic into
        each sub-class.
        """
        msg = e.args[0]

        common_startswith = (WorkUnitCancelError, WorkUnitResultsError, WorkUnitError)

        for klass in common_startswith:
            if msg.startswith(klass._MESSAGE):
                work_unit_id = msg[len(klass._MESSAGE) :]
                return klass(work_unit_id, node=node, state_name=state_name)

        return UnknownError(msg, node=node, state_name=state_name)


def receptor_config_exists():
    return os.path.exists(__RECEPTOR_CONF)


def read_receptor_config():
    # for K8S deployments, getting a lock is necessary as another process
    # may be re-writing the config at this time
    if settings.IS_K8S:
        lock = FileLock(__RECEPTOR_CONF_LOCKFILE)
        with lock:
            with open(__RECEPTOR_CONF, 'r') as f:
                return yaml.safe_load(f)
    else:
        with open(__RECEPTOR_CONF, 'r') as f:
            return yaml.safe_load(f)


def work_signing_enabled(config_data):
    for section in config_data:
        if 'work-signing' in section:
            return True
    return False


def get_receptor_sockfile(config_data):
    for section in config_data:
        for entry_name, entry_data in section.items():
            if entry_name == 'control-service':
                if 'filename' in entry_data:
                    return entry_data['filename']
                else:
                    raise RuntimeError(f'Receptor conf {__RECEPTOR_CONF} control-service entry does not have a filename parameter')
    else:
        raise RuntimeError(f'Receptor conf {__RECEPTOR_CONF} does not have control-service entry needed to get sockfile')


def get_tls_client(config_data, use_stream_tls=None):
    if not use_stream_tls:
        return None

    for section in config_data:
        for entry_name, entry_data in section.items():
            if entry_name == 'tls-client':
                if 'name' in entry_data:
                    return entry_data['name']
    return None


def get_receptor_ctl(config_data=None):
    if config_data is None:
        config_data = read_receptor_config()
    receptor_sockfile = get_receptor_sockfile(config_data)
    try:
        return ReceptorControl(receptor_sockfile, config=__RECEPTOR_CONF, tlsclient=get_tls_client(config_data, True))
    except RuntimeError:
        return ReceptorControl(receptor_sockfile)


def adopt_remote_work(receptor_ctl, node, unit_id, config_data=None):
    """Adopt a running work unit from a remote node, passing TLS/signwork when configured.

    PR#1564 adds adopt_work() to receptorctl. If not available (older client), falls back
    to the JSON control-socket protocol directly — compatible with any PR#1564 receptor server.

    TEMPORARY: Once receptor#1564 becomes the minimum required version and requirements.txt
    is updated, the fallback block (lines ~197–206) can be removed since adopt_work() will
    always be available. This handles mixed-version deployments during transition.
    """
    if config_data is None:
        config_data = read_receptor_config()
    tls_client = get_tls_client(config_data, True)
    sign = work_signing_enabled(config_data)

    if hasattr(receptor_ctl, 'adopt_work'):
        return receptor_ctl.adopt_work(node, unit_id, tlsclient=tls_client or None, signwork=sign)

    # TODO: Delete this fallback block once receptor#1564 is the minimum required version.
    # Older receptorctl: send JSON directly so the server's InitFromJSON path handles TLS/signwork.
    # The text-protocol InitFromString path does NOT support tlsclient/signwork.
    command = {"command": "work", "subcommand": "adopt", "node": node, "unitid": unit_id}
    if tls_client:
        command["tlsclient"] = tls_client
    if sign:
        # Must be the string "true", not a JSON bool: receptor's boolFromMap() does
        # value.(string) and accepts only "true"/"false". A bool fails the assertion,
        # the adopt handler swallows the error and defaults to signWork=false, and the
        # adopted unit then requests `work results` unsigned — which the remote rejects,
        # leaving the stream at 0 bytes forever. receptorctl's own submit_work() sends
        # the string for the same reason.
        command["signwork"] = "true"
    receptor_ctl.connect()
    receptor_ctl.writestr(json.dumps(command) + "\n")
    return receptor_ctl.read_and_parse_json()


def find_node_in_mesh(node_name, receptor_ctl):
    attempts = 10
    backoff = 1
    for attempt in range(attempts):
        all_nodes = receptor_ctl.simple_command("status").get('Advertisements', None)
        for node in all_nodes:
            if node.get('NodeID') == node_name:
                return node
        else:
            logger.warning(f"Instance {node_name} is not in the receptor mesh. {attempts - attempt} attempts left.")
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


def run_until_complete(node, timing_data=None, worktype='ansible-runner', ttl='20s', **kwargs):
    """
    Runs an ansible-runner work_type on remote node, waits until it completes, then returns stdout.
    """

    config_data = read_receptor_config()
    receptor_ctl = get_receptor_ctl(config_data)

    use_stream_tls = getattr(get_conn_type(node, receptor_ctl), 'name', None) == "STREAMTLS"
    kwargs.setdefault('tlsclient', get_tls_client(config_data, use_stream_tls))
    if ttl is not None:
        kwargs['ttl'] = ttl
    kwargs.setdefault('payload', '')
    if work_signing_enabled(config_data):
        kwargs['signwork'] = True

    transmit_start = time.time()
    result = receptor_ctl.submit_work(worktype=worktype, node=node, **kwargs)

    unit_id = result['unitid']
    run_start = time.time()
    if timing_data:
        timing_data['transmit_timing'] = run_start - transmit_start
    run_timing = 0.0
    stdout = ''
    state_name = 'local var never set'

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

    except RuntimeError as e:
        receptor_e = FuzzyError(e, node, state_name)
        if type(receptor_e) in (
            WorkUnitError,
            WorkUnitResultsError,
        ):
            logger.warning(f'While consuming job results: {receptor_e}')
        else:
            raise
    finally:
        if settings.RECEPTOR_RELEASE_WORK:
            try:
                res = receptor_ctl.simple_command(f"work release {unit_id}")

                if res != {'released': unit_id}:
                    logger.warning(f'Could not confirm release of receptor work unit id {unit_id} from {node}, data: {res}')

                receptor_ctl.close()
            except RuntimeError as e:
                receptor_e = FuzzyError(e, node, state_name)
                if type(receptor_e) in (
                    WorkUnitError,
                    WorkUnitCancelError,
                ):
                    logger.warning(f"While releasing work: {receptor_e}")
                else:
                    logger.error(f"While releasing work: {receptor_e}")

    if state_name.lower() == 'failed':
        work_detail = status.get('Detail', '')
        if work_detail:
            if stdout:
                raise RemoteJobError(f'Receptor error from {node}, detail:\n{work_detail}\nstdout:\n{stdout}')
            else:
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

    except Exception as exc:
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
            args.append('--{} {}'.format(option.replace('_', '-'), ' '.join(f'"{item}"' for item in vargs.get(option))))
    for option in ('file_pattern', 'image_prune', 'process_isolation_executable', 'grace_period'):
        if vargs.get(option) is True:
            args.append('--{}'.format(option.replace('_', '-')))
        elif vargs.get(option) not in (None, ''):
            args.append('--{}={}'.format(option.replace('_', '-'), vargs.get(option)))
    return args


def worker_cleanup(node_name, vargs):
    args = _convert_args_to_cli(vargs)

    remote_command = ' '.join(args)
    logger.debug(f'Running command over receptor mesh on {node_name}: ansible-runner worker {remote_command}')

    stdout = run_until_complete(node=node_name, params={"params": remote_command})

    return stdout


class _CountingReader:
    """Wrap the receptor results sockfile so the caller can see stream progress.

    The process streamer runs in its own thread and gives no indication of how much it
    has consumed, which is the only way to tell a stream that is merely quiet apart from
    one that will never deliver anything. Only readline() is used by ansible-runner's
    Processor today; read() and the attribute proxy keep the wrapper transparent if that
    changes.
    """

    def __init__(self, fileobj):
        self._f = fileobj
        self.bytes_read = 0
        self.last_progress = time.monotonic()

    def _record(self, data):
        if data:
            self.bytes_read += len(data)
            self.last_progress = time.monotonic()
        return data

    def readline(self, *args):
        return self._record(self._f.readline(*args))

    def read(self, *args):
        return self._record(self._f.read(*args))

    def __getattr__(self, name):
        return getattr(self._f, name)


class AWXReceptorJob:
    # Set by _process_phase when it walked away from a still-running work unit instead of
    # canceling it; see _cancel_unit_on_signal. Callers must then leave the job 'running'
    # with its work_unit_id, and must not finalize or release it — that state is what lets
    # the unit be adopted again.
    detached = False

    # Seconds the results stream may sit idle *while the work unit is already terminal*
    # before _await_processor gives up on it. Left None for normal job submission, where
    # _run_internal owns the unit's whole lifecycle and a quiet stream is just a quiet job.
    # Only adoption can inherit a unit whose stdout transport is already dead, so only
    # reattach_to_work_unit sets this.
    stream_idle_timeout = None

    # Set by _await_processor when it abandoned such a stream. The job is not failed —
    # the output still exists on the execution node — so the caller must decide between
    # retrying later and finalizing from the work unit status.
    stream_stalled = False

    # How often to re-check a stream that has not finished yet.
    STREAM_POLL_INTERVAL = 10

    TERMINAL_UNIT_STATES = ('Succeeded', 'Failed', 'Canceled')

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
        self.config_data = read_receptor_config()
        self.receptor_ctl = get_receptor_ctl(self.config_data)
        return self._run_internal(self.receptor_ctl)

    def _receptor_release_work(self, receptor_ctl: ReceptorControl, status: str) -> None:
        if self.unit_id is None:
            return

        if settings.RECEPTOR_RELEASE_WORK is False:
            return

        if settings.RECEPTOR_KEEP_WORK_ON_ERROR and status == 'error':
            return

        try:
            receptor_ctl.simple_command(f"work release {self.unit_id}")
            logger.debug(f"Released work unit {self.unit_id}.")
        except Exception:
            logger.exception(f"Error releasing work unit {self.unit_id}.")

    def _run_internal(self, receptor_ctl):
        self._transmit_phase(receptor_ctl)
        return self._process_phase(receptor_ctl)

    def _transmit_phase(self, receptor_ctl):
        """Submit work to receptor and wait for the transmit thread to finish.

        Creates the receptor work unit, streams the job payload (private_data_dir + kwargs)
        to the EE via a socketpair, and saves the resulting unit_id to the DB.

        After this returns, artifacts/ is deleted from private_data_dir. Fact-cache and
        other input artifacts are transmitted to the EE during this phase; by the time
        _process_phase() reads artifacts output, the dir is empty so there is no stale
        input state. This means _process_phase() always receives a clean private_data_dir
        whether called from _run_internal() or from reattach_to_work_unit().
        """
        # Create a socketpair. Where the left side will be used for writing our payload
        # (private data dir, kwargs). The right side will be passed to Receptor for
        # reading.
        sockin, sockout = socket.socketpair()

        # Prepare the submit_work kwargs before creating threads, because references to settings are not thread-safe
        work_submit_kw = dict(worktype=self.work_type, params=self.receptor_params, signwork=self.sign_work)
        if self.work_type == 'ansible-runner':
            work_submit_kw['node'] = self.task.instance.execution_node
            use_stream_tls = get_conn_type(work_submit_kw['node'], receptor_ctl).name == "STREAMTLS"
            work_submit_kw['tlsclient'] = get_tls_client(self.config_data, use_stream_tls)

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
            failpoint('job.after_submit_before_unit_saved', job_id=self.task.instance.pk, unit_id=result['unitid'])
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

    def _cancel_unit_on_signal(self):
        """Should the signal that interrupted this stream also cancel the receptor work unit?

        Only if the user asked for the job to stop — and the signal cannot tell us that.
        dispatcherd sends SIGUSR1 both for a targeted cancel and for every worker it is
        "canceling for shutdown", so on a controller restart every running job is signaled
        with SIGUSR1 and nothing else. Reading SIGUSR1 as a cancel therefore kills a healthy
        EE on every pod restart, which is the exact failure adoption exists to prevent.

        The job row is the authority instead. UnifiedJob.cancel() commits cancel_flag before
        it signals the dispatcher, specifically so this process can tell a cancel from a
        shutdown, and BaseTask.run() already draws the same distinction from the same flag.

        A shutdown is a statement about this controller, not about the job: the EE is on
        another node and still working, so leaving the unit alive is what lets
        _process_running_jobs hand the stream to whichever controller comes back first. If
        the flag cannot be read, detach — an unfinalized job can be adopted again, a killed
        EE cannot be un-killed.
        """
        job = self.task.instance
        try:
            job.refresh_from_db(fields=['cancel_flag'])
        except Exception:
            logger.warning(f'Could not read cancel_flag for {job.log_format}; detaching from work unit {self.unit_id}')
            return False
        return bool(job.cancel_flag)

    def _stream_is_stalled(self, receptor_ctl, reader):
        """Has the work unit finished without its output ever reaching us?

        Both halves are required. A terminal unit on its own proves nothing — the final
        bytes legitimately arrive after the state flips. Idleness on its own proves
        nothing either — a running job can go hours between events. It is the pair, plus
        a byte count short of the unit's own StdoutSize, that identifies a stream whose
        remaining bytes are never coming.
        """
        if time.monotonic() - reader.last_progress < self.stream_idle_timeout:
            return False
        try:
            unit_status = receptor_ctl.simple_command(f'work status {self.unit_id}')
        except Exception:
            # Without a status there is nothing to compare against, and a stream that is
            # still healthy would be thrown away on a guess. Keep waiting.
            return False
        if unit_status.get('StateName') not in self.TERMINAL_UNIT_STATES:
            return False
        return reader.bytes_read < unit_status.get('StdoutSize', 0)

    def _await_processor(self, processor_future, receptor_ctl, reader, resultsock):
        """Wait for the process streamer, abandoning a stream that can never complete.

        Receptor can adopt a work unit's metadata while its stdout monitor never manages
        to connect to the execution node. The results stream then yields nothing and
        never reaches EOF, so an unguarded wait holds the dispatcher worker forever.
        """
        if self.stream_idle_timeout is None:
            return processor_future.result()

        while True:
            try:
                return processor_future.result(timeout=self.STREAM_POLL_INTERVAL)
            except concurrent.futures.TimeoutError:
                pass
            if self._stream_is_stalled(receptor_ctl, reader):
                self.stream_stalled = True
                logger.warning(
                    f'Work unit {self.unit_id} is terminal but its results stream delivered only '
                    f'{reader.bytes_read} bytes and has been idle for {self.stream_idle_timeout}s; '
                    f'abandoning the stream'
                )
                # Yanking the socket is what unblocks the processor thread's readline();
                # the SignalExit path below relies on the same thing.
                try:
                    resultsock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    return processor_future.result(timeout=self.STREAM_POLL_INTERVAL)
                except concurrent.futures.TimeoutError:
                    logger.error(f'Work unit {self.unit_id}: processor thread did not exit after socket shutdown; abandoning')
                    return None

    def _process_phase(self, receptor_ctl):
        """Stream events from the receptor work unit via the ansible-runner process streamer.

        Extracted from _run_internal() so it can be called standalone for job adoption
        after a same-controller restart (reattach_to_work_unit). The transmit phase
        (submit_work + transmit) is not repeated — the EE is already running.
        """
        resultsock = None
        resultfile = None
        try:
            resultsock, resultfile = receptor_ctl.get_work_results(self.unit_id, return_socket=True, return_sockfile=True)
        except Exception:
            logger.exception(f'Failed to get work results for unit {self.unit_id}')
            raise

        reader = _CountingReader(resultfile)
        failpoint('job.stream_started', job_id=self.task.instance.pk, unit_id=self.unit_id)

        connections.close_all()

        # "processor" and the main thread will be separate threads.
        # If a cancel happens, the main thread will encounter an exception, in which case
        # we yank the socket out from underneath the processor, which will cause it to exit.
        # The ThreadPoolExecutor context manager ensures we do not leave any threads laying around.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            processor_future = executor.submit(self.processor, reader)

            try:
                signal_state.raise_exception = True
                # address race condition where SIGTERM was issued after this dispatcher task started
                if signal_callback():
                    raise SignalExit()
                res = self._await_processor(processor_future, receptor_ctl, reader, resultsock)
            except SignalExit:
                # Nothing below may raise. The signal that got us here is usually this pod
                # shutting down, so the receptor control socket and the results socket are
                # dying at the same moment and any of these calls can fail. An escape lands
                # in BaseTask.run()'s generic handler, which records the job 'error' and
                # clears the running + work_unit_id pair the orphan scan matches on —
                # stranding the live EE whichever way we decided here.
                if self._cancel_unit_on_signal():
                    try:
                        receptor_ctl.simple_command(f"work cancel {self.unit_id}")
                    except Exception:
                        logger.warning(f'Could not cancel work unit {self.unit_id}; it may outlive this controller')
                else:
                    self.detached = True
                    logger.info(f'Detaching from work unit {self.unit_id} without canceling it')
                if resultsock:
                    try:
                        resultsock.shutdown(socket.SHUT_RDWR)
                    except Exception:
                        pass
                if resultfile:
                    try:
                        resultfile.close()
                    except Exception:
                        pass
                result = namedtuple('result', ['status', 'rc'])
                res = result('canceled', 1)
            finally:
                signal_state.raise_exception = False

            if res.status == 'error':
                return self._handle_work_error(receptor_ctl, res)

        return res

    def _handle_work_error(self, receptor_ctl, res):
        """Handle the error path from _process_phase when the work unit status is 'error'."""
        # If ansible-runner ran, but an error occured at runtime, the traceback information
        # is saved via the status_handler passed in to the processor.
        if 'result_traceback' in self.task.runner_callback.extra_update_fields:
            return res

        status_unknown = False
        try:
            unit_status = receptor_ctl.simple_command(f'work status {self.unit_id}')
            detail = unit_status.get('Detail') or ''
            state_name = unit_status.get('StateName', None)
            stdout_size = unit_status.get('StdoutSize', 0)
        except Exception:
            detail = ''
            state_name = ''
            stdout_size = 0
            status_unknown = True
            logger.exception(f'An error was encountered while getting status for work unit {self.unit_id}')

        if status_unknown and not self._cancel_unit_on_signal():
            # We reached here because the results stream reported an error, but the control
            # socket that could confirm it is unreachable — and unreachable is not failed.
            # That pair is the ordinary shape of this controller shutting down: receptor
            # lives in a sibling container going down alongside us, so the stream breaking
            # says something about this pod, not about the EE on another node. Recording
            # the error would clear the running + work_unit_id pair the orphan scan matches
            # on, so detach for the same reason the signal path does and let the job be
            # adopted. A canceled job is excluded — it is meant to stop.
            self.detached = True
            logger.info(f'Work unit {self.unit_id} reported an error but its status is unreachable; detaching instead of failing the job')
            return res

        if 'exceeded quota' in detail:
            logger.warning(detail)
            log_name = self.task.instance.log_format
            logger.warning(f"Could not launch pod for {log_name}. Exceeded quota.")
            self.task.update_model(self.task.instance.pk, status='pending')
            return None

        try:
            receptor_output = ''
            if state_name == 'Failed' and self.task.runner_callback.event_ct == 0:
                # if receptor work unit failed and no events were emitted, work results may
                # contain useful information about why the job failed. In case stdout is
                # massive, only ask for last 1000 bytes
                startpos = max(stdout_size - 1000, 0)
                _resultsock, resultfile = receptor_ctl.get_work_results(self.unit_id, startpos=startpos, return_socket=True, return_sockfile=True)
                lines = resultfile.readlines()
                receptor_output = b"".join(lines).decode()
                _resultsock.shutdown(socket.SHUT_RDWR)
            if receptor_output:
                self.task.runner_callback.delay_update(result_traceback=f'Worker output:\n{receptor_output}')
            elif detail:
                self.task.runner_callback.delay_update(result_traceback=f'Receptor detail:\n{detail}')
            else:
                logger.warning(f'No result details or output from {self.task.instance.log_format}, status:\n{state_name}')
        except Exception:
            logger.exception(f'Work results error from job id={self.task.instance.id} work_unit={self.task.instance.work_unit_id}')
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
            artifacts_handler=self.task.runner_callback.artifacts_handler,
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

    def submit_pod_attach(self, receptor_ctl, pod_name, pod_namespace):
        """Submit a work unit that attaches to a container-group pod that is already running.

        The pod outlived the controller that created it, so there is nothing left to create —
        only something to watch. receptor's kube worker has always had that branch: a non-empty
        ``ExtraData.PodName`` makes ``RunWorkUsingLogger`` get the existing pod and skip stdin,
        because the pod already received its private data dir. Until the ``pod_name`` runtime
        param it was reachable only via ``Restart()`` on the node that created the pod.

        Going back through receptor rather than reading the pod log directly is what keeps the
        rest of the lifecycle intact: the unit streams live, ``work cancel`` reaches the pod,
        and ``work release`` deletes it — all the same code the mesh path uses.

        The payload is empty on purpose. skipStdin means receptor never reads it, and sending
        the private data dir again would be wrong even if it did: this pod's worker consumed
        its stdin once and closed it (``StdinOnce``).
        """
        params = {'pod_name': pod_name, 'kube_namespace': pod_namespace}
        if self.credential:
            params['secret_kube_config'] = yaml.dump(self.kube_config, explicit_start=True)

        result = receptor_ctl.submit_work(worktype=self.work_type, params=params, signwork=self.sign_work, payload=io.BytesIO(b''))
        self.unit_id = result['unitid']
        return self.unit_id

    @property
    def sign_work(self):
        if self.work_type in ('ansible-runner', 'local'):
            return work_signing_enabled(self.config_data)
        return False

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

        if settings.AWX_RUNNER_KEEPALIVE_SECONDS:
            pod_spec['spec']['containers'][0].setdefault('env', [])
            pod_spec['spec']['containers'][0]['env'].append({'name': 'ANSIBLE_RUNNER_KEEPALIVE_SECONDS', 'value': str(settings.AWX_RUNNER_KEEPALIVE_SECONDS)})

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


# TODO: receptor reload expects ordering within config items to be preserved
# if python dictionary is not preserving order properly, may need to find a
# solution. yaml.dump does not seem to work well with OrderedDict. below line may help
# yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))
#
RECEPTOR_CONFIG_STARTER = (
    {'local-only': None},
    {'log-level': settings.RECEPTOR_LOG_LEVEL},
    {'node': {'firewallrules': [{'action': 'reject', 'tonode': settings.CLUSTER_HOST_ID, 'toservice': 'control'}]}},
    {'control-service': {'service': 'control', 'filename': '/var/run/receptor/receptor.sock', 'permissions': '0660'}},
    {'work-command': {'worktype': 'local', 'command': 'ansible-runner', 'params': 'worker', 'allowruntimeparams': True}},
    {'work-signing': {'privatekey': '/etc/receptor/work_private_key.pem', 'tokenexpiration': '1m'}},
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
            'rootcas': '/etc/receptor/tls/ca/mesh-CA.crt',
            'cert': '/etc/receptor/tls/receptor.crt',
            'key': '/etc/receptor/tls/receptor.key',
            'mintls13': False,
        }
    },
)


class _AdoptionTask:
    """Minimal task stub passed to AWXReceptorJob when called from reattach_to_work_unit.

    Stands in for BaseTask without re-executing task-manager logic. update_model is a
    no-op since adoption doesn't touch scheduling fields (those are handled by the
    reaper/heartbeat path that triggered the adoption).
    """

    def __init__(self, instance, runner_callback):
        self.instance = instance
        self.runner_callback = runner_callback
        self.private_data_dir = None  # Set by reattach_to_work_unit before finalization

    def build_execution_environment_params(self, _instance, _private_data_dir):
        return {}

    def update_model(self, pk, **kwargs):
        # Intentionally a no-op: adoption reuses _process_phase without task-manager field updates.
        # Heartbeat/reaper handles scheduling state; no fields need updating here.
        pass


def _get_adoption_exit_code(unit_status, state_name):
    """Extract exit code from a finished receptor work unit status dict."""
    if 'ExitCode' in unit_status:
        return unit_status['ExitCode']
    detail = unit_status.get('Detail', '')
    try:
        return int(detail.split()[-1])
    except (ValueError, IndexError):
        return 0 if state_name == 'Succeeded' else 1


def _build_adoption_callback(job, dedup_threshold, collision_zone):
    """Construct a RunnerCallback for event replay during adoption."""
    callback = RunnerCallback.create_for_job(
        job,
        safe_env=dict(job.job_env or {}),
        dedup_threshold=dedup_threshold,
        persisted_counters=collision_zone,
    )
    # Normal runs get host_map for free from build_inventory. Adoption writes no inventory
    # file, so it has to source the same data itself or replayed events lose host_id.
    callback.populate_host_map_from_inventory(job)
    return callback


def _get_or_create_private_data_dir(job):
    """Return a writable private_data_dir for the adoption process streamer.

    On same-controller restart the original tempdir may be gone (e.g. on OCP where /tmp
    is wiped on pod restart). ansible-runner's process streamer only needs a writable root
    directory — it creates artifacts/job_events/ itself.

    Uses AWX_ISOLATION_BASE_PATH (the same root as all other job working dirs) so that
    sysadmin-configured isolation paths (e.g. persistent volumes on OCP) are respected.
    """
    return tempfile.mkdtemp(
        prefix=JOB_FOLDER_PREFIX % job.pk + 'adoption_',
        dir=settings.AWX_ISOLATION_BASE_PATH,
    )


def _adopted_finished_at(job, callback=None):
    """When the job *actually* ended, for an adopted job, plus the adoption lag in seconds.

    On the normal path `finished` is set to `now()` at the moment the controller commits the
    terminal status, which is within a second of the playbook ending. Adoption breaks that
    equivalence: the job keeps running on its execution node while its controller is dead, and
    nobody writes a terminal status until an adopter picks it up. Observed on hadr-rosa-a that
    is 90-180 s, and it lands on every job the dead controller owned at once — 24 jobs stamped
    inside a 2.6 s window, each inflated by its own share of the gap. A 27 s playbook reported
    207 s elapsed (job 2392528). Left alone it silently corrupts every duration measurement
    taken across a controller failure, which is exactly when we most want to measure.

    The wrapup event's `created` is the right source. It is the *execution node's* clock,
    carried in the runner payload, so it marks when the work really finished rather than when
    we noticed, and it covers both adoption paths — a container-group pod's
    `terminated.finishedAt` would be equally authoritative but does not exist for mesh jobs,
    and k8s truncates it to whole seconds.

    It has to come from the callback, which saw the event stream in this process, and not from
    a query. Event persistence is asynchronous, so when this runs only a prefix of the adopted
    job's events has reached the database: a `Max('created')` here came back ~194 s short of
    the real end on hadr-rosa-a and back-dated `finished` into the middle of the run. The
    queryset is still worth consulting as a second choice — on a re-adoption the events from
    the earlier attempt are long since persisted and this process may never see a wrapup event.

    Two guards, because this is the one place a second clock enters the model:
    - clamped to `[job.started, now()]`, so skew between the controller and a mesh execution
      node can never produce a negative `elapsed` or a timestamp in the future;
    - falls back to `now()` when neither source has anything, which is the wedged-pod case —
      there the gap is real work time, not measurement lag.
    """
    right_now = now()

    # Runner hands `created` over as an ISO string. Throw out anything unparseable rather than
    # letting it abort the finalization — the same bargain JobEvent.create_from_data makes, and
    # the consequence of losing it here is only a less accurate `finished`.
    ended_at = getattr(callback, 'wrapup_event_created', None)
    if ended_at is not None and not isinstance(ended_at, datetime):
        try:
            ended_at = parse_datetime(ended_at)
        except (TypeError, ValueError):
            ended_at = None
    if ended_at is not None and ended_at.tzinfo is None:
        ended_at = ended_at.replace(tzinfo=timezone.utc)

    if ended_at is None:
        ended_at = job.get_event_queryset().aggregate(last=Max('created'))['last']
    if ended_at is None:
        return right_now, 0.0

    finished_at = min(max(ended_at, job.started or ended_at), right_now)
    return finished_at, (right_now - finished_at).total_seconds()


def _finalize_adopted_job(job, callback, exit_code, process_phase_failed, final_status=None):
    """Commit terminal status for an adopted job via the shared _finalize_job_run path.

    The shared finalization function uses duck typing to schedule task/workflow managers
    for speculative dependencies and workflow jobs.

    Guards before calling: if awx_receptor_workunit_reaper already committed the final
    status, there is nothing left to do.

    Args:
        final_status: overrides the status derived from exit_code. Used for a cancel, which
            is a nonzero exit that must not be reported as a failure.
    """
    from awx.main.tasks.jobs import _finalize_job_run

    job.refresh_from_db(fields=['status'])
    if job.status != 'running':
        return

    final_status = final_status or ('successful' if exit_code == 0 else 'failed')
    finished_at, adoption_lag = _adopted_finished_at(job, callback)
    extra = {'finished': finished_at}
    if job.started:
        extra['elapsed'] = (finished_at - job.started).total_seconds()

    # Record adoption metadata in job_explanation (must be before finalization). Both paths
    # through this function are adoptions, and which controller took the job over matters
    # most when the process phase raised, so this is unconditional.
    # Goes through delay_update rather than extra_fields: _finalize_job_run applies
    # extra_fields on top of the delayed fields, so setting it here would discard any
    # explanation status_handler recorded for the real failure. delay_update appends.
    # settings.CLUSTER_HOST_ID rather than Instance.objects.me().hostname: me() looks the row
    # up *by* CLUSTER_HOST_ID, so the two are the same string, and me() additionally raises
    # when no row matches. Letting that escape would skip finalization while the caller's
    # `finally` still releases the work unit, stranding the job in `running` forever.
    surviving_controller = settings.CLUSTER_HOST_ID
    callback.delay_update(job_explanation=f'Job adopted by {surviving_controller}. Work unit: {job.work_unit_id}. Execution node: {job.execution_node}.')

    _finalize_job_run(type(job), job.pk, callback, final_status, extra_fields=extra)

    label = 'exit_code (process phase raised)' if process_phase_failed else 'adoption'
    # adoption_lag is no longer visible in `finished` now that it is back-dated, and it is the
    # recovery SLO for this whole feature — how long a job sat done-but-uncommitted after its
    # controller died. Keep it where it can still be measured.
    logger.info(f'Job {job.id} finalized via {label}: {final_status} (adoption lag {adoption_lag:.1f}s)')


def _compute_adoption_dedup(job):
    """Return (safe_threshold, collision_zone, persisted_ct) for counter-skip dedup during adoption.

    Hybrid approach — memory is O(1) + O(worker_count), never O(total events):

    safe_threshold: highest counter where all lower counters are also in DB (contiguous
        prefix starting from counter 1). Events <= this are skipped with a single integer comparison.

    collision_zone: small set of counters above safe_threshold that ARE in DB. These
        exist because parallel callback workers can commit a higher-counter event before
        a lower-counter one. Bounded by JOB_EVENT_WORKERS × batch size, typically < 20
        regardless of total job event count.

    persisted_ct: how many events are already in the DB, counted in the database and
        including any beyond the cap. Seeds callback.event_ct, which would otherwise
        undercount precisely when the collision zone is truncated.
    """
    qs = job.get_event_queryset()

    # The contiguous prefix has to be anchored at counter 1 — if the first event never
    # committed, every later counter sits after a gap and none of them can be skipped.
    # Two constant-cost queries: one anchor check, one "lowest counter whose successor is
    # missing". Walking the counters in windows instead would cost a query per window and
    # fetch every row, on every adoption attempt.
    if not qs.filter(counter=1).exists():
        safe_threshold = 0
    else:
        next_ctr = qs.filter(counter=OuterRef('counter') + 1)
        gap_event = qs.annotate(has_next=Exists(next_ctr)).filter(has_next=False).order_by('counter').first()
        safe_threshold = gap_event.counter if gap_event else 0

    cap = settings.JOB_EVENT_WORKERS * settings.JOB_EVENT_CALLBACK_BUFFER_SIZE
    above_threshold = qs.filter(counter__gt=safe_threshold)
    # count() in the database rather than len(list(...)): an early gap leaves nearly every
    # event above the threshold, and materializing that list is the OOM this cap exists to
    # prevent. Slicing the queryset lets the DB apply the limit too.
    persisted_above = above_threshold.count()

    if persisted_above > cap:
        logger.warning(
            f'Job {job.id}: collision_zone has {persisted_above} events above safe_threshold, '
            f'exceeds dedup cap of {cap}. Events beyond the cap may be re-processed if replayed. '
            f'Consider increasing JOB_EVENT_CALLBACK_BUFFER_SIZE or reducing parallel callback workers.'
        )

    # order_by keeps truncation deterministic and retains the counters closest to the
    # contiguous prefix; slicing an unordered queryset would drop arbitrary rows.
    collision_zone = set(above_threshold.order_by('counter').values_list('counter', flat=True)[:cap])
    return safe_threshold, collision_zone, safe_threshold + persisted_above


def _adoption_stall_budget_exhausted(job):
    """Has this job gone without new events for longer than HADR_JOB_ADOPTION_TIMEOUT?

    Bounds how long a stalled results stream may be retried. Reuses the orphan-age
    measure from adopt_job_async's unreachable-unit branch so the two ways an adoption
    can fail to make progress converge on one deadline instead of two that can disagree.

    With no timestamp to measure from there is no deadline to be past, so the caller
    keeps deferring rather than finalizing on a guess.
    """
    last_event_time = job.get_event_queryset().aggregate(Max('created'))['created__max']
    orphaned_since = last_event_time or job.started
    if not orphaned_since:
        return False
    return orphaned_since < now() - timedelta(seconds=settings.HADR_JOB_ADOPTION_TIMEOUT)


def get_adoption_unit_status(receptor_ctl, job):
    """Return the receptor work unit status dict for an adoption attempt.

    Asks this controller's own receptor first. The unit is local whenever this controller
    submitted the work (same-controller restart, where execution_node is a remote EE but
    the proxy unit lives here) or already adopted it on an earlier heartbeat. Adopting a
    unit this receptor already holds would be a pointless round trip to the execution node,
    and only the local query reports a real StateName — `work adopt` answers
    'Already Adopted' with no state.

    Falls back to adopting from the execution node when the local receptor does not know
    the unit: the genuine cross-controller case, and the case where this controller's unit
    directory was lost (e.g. /tmp wiped on an OCP pod restart).
    """
    unit_id = job.work_unit_id
    failpoint('adoption.unit_status', job_id=job.id, unit_id=unit_id)
    try:
        return receptor_ctl.simple_command(f'work status {unit_id}')
    except Exception:
        if not job.execution_node or job.execution_node == settings.CLUSTER_HOST_ID:
            raise
        logger.info(f'Job {job.id}: unit {unit_id} unknown to local receptor, adopting from execution node {job.execution_node}')
        return adopt_remote_work(receptor_ctl, job.execution_node, unit_id)


def _determine_adoption_status_from_res(res):
    """Extract status and exit code from process result."""
    res_status = getattr(res, 'status', '')
    if res_status == 'canceled':
        return 'canceled', 1
    status = 'successful' if res_status == 'successful' else 'failed'
    exit_code = 0 if res_status == 'successful' else 1
    return status, exit_code


def _determine_adoption_status_from_unit(job, receptor_ctl, unit_id):
    """Query work unit status and determine job status, or defer if not terminal."""
    try:
        unit_status = receptor_ctl.simple_command(f'work status {unit_id}')
        state_name = unit_status.get('StateName', '')
    except Exception:
        logger.debug(f'Could not get final status for {unit_id} after process phase failure')
        unit_status = {}
        state_name = ''

    if state_name not in ('Succeeded', 'Failed', 'Canceled'):
        logger.info(f'Job {job.id}: stream failed but unit still in {state_name!r} state, deferring adoption for retry on next heartbeat')
        return None, None, False

    exit_code = _get_adoption_exit_code(unit_status, state_name)
    status = 'failed' if exit_code != 0 else 'successful'
    return status, exit_code, True


def _finalize_adoption_result(job, callback, res, process_phase_failed, receptor_ctl, unit_id, private_data_dir):
    """Finalize a job after adoption completes or fails.

    Calls post-run hooks (if any) before marking status terminal.

    Args:
        private_data_dir: The adoption's private_data_dir for hook execution

    Returns:
        True if job was finalized (terminal status),
        False if adoption was deferred (unit still running),
        None if job was already handled (e.g., quota exceeded in _handle_work_error)
    """
    if res is not None:
        status, exit_code = _determine_adoption_status_from_res(res)
    elif not process_phase_failed:
        logger.info(f'Job {job.id}: adoption deferred (handled in _handle_work_error)')
        return None
    else:
        status, exit_code, should_finalize = _determine_adoption_status_from_unit(job, receptor_ctl, unit_id)
        if not should_finalize:
            return False

    # Call post-run hooks before finalization
    hook_succeeded, hook_error = invoke_adoption_hooks(job, callback, private_data_dir, status)
    if not hook_succeeded:
        status = hook_error.get('status_override', 'failed')
        exit_code = 1
        if hook_error.get('explanation'):
            callback.delay_update(job_explanation=hook_error['explanation'])
        if hook_error.get('traceback'):
            callback.delay_update(result_traceback=hook_error['traceback'])

    _finalize_adopted_job(job, callback, exit_code, process_phase_failed, final_status=status)
    return True


def reattach_to_work_unit(job, receptor_ctl, unit_status=None):
    """Reconnect to a receptor work unit and stream events in real-time until it completes.

    Reconstructs the minimal process-phase context from the DB job record, then calls
    _process_phase which blocks until the work unit finishes — streaming events live as
    the EE generates them. Dedup (safe_threshold + collision_zone) skips events already
    in DB so replay from startpos=0 is safe.

    Intended to be called from adopt_job_async (a background task) so the caller is not
    blocked. Supports cross-controller adoption via job.execution_node (AAP-89602).

    Args:
        unit_status: Optional pre-fetched work unit status dict (avoids duplicate adopt_remote_work calls)

    Returns:
        True if the job reached a terminal status here, False if it is still running and
        should be adopted again later (status unreadable, or this controller shut down
        mid-stream).
    """
    unit_id = job.work_unit_id

    try:
        if unit_status is None:
            unit_status = get_adoption_unit_status(receptor_ctl, job)
        state_name = unit_status.get('StateName', '')
        logger.info(f'Adopting job {job.id}: unit {unit_id} in state {state_name!r}, starting real-time streaming')
    except Exception:
        logger.warning(f'Cannot get receptor status for work unit {unit_id} (job {job.id}, execution_node={job.execution_node}), deferring adoption')
        return False

    # Pending and Running are streamed, not deferred. get_work_results blocks until the unit
    # produces output, which is exactly what _run_internal does the moment it submits work —
    # the unit is Pending there too. Waiting for a terminal state instead would hold every
    # event back until the job ended, and for a remotely adopted unit that is the one window
    # where receptor can lose the final stdout flush.
    safe_threshold, collision_zone, persisted_ct = _compute_adoption_dedup(job)
    failpoint('adoption.after_snapshot', job_id=job.id, safe_threshold=safe_threshold, persisted=persisted_ct)
    max_counter = max(collision_zone) if collision_zone else safe_threshold
    logger.info(
        f'Job {job.id}: safe_threshold={safe_threshold} collision_zone_size={len(collision_zone)} '
        f'(max counter={max_counter}), replaying from startpos=0 with counter-skip'
    )

    callback = _build_adoption_callback(job, safe_threshold, collision_zone)
    # Account for events already persisted so emitted_events / EOF final_counter reflect the
    # full job. Uses the DB count rather than len(collision_zone), which is capped.
    callback.event_ct = persisted_ct

    private_data_dir = _get_or_create_private_data_dir(job)
    adoption_task = _AdoptionTask(job, callback)
    adoption_task.private_data_dir = private_data_dir  # Available to final_run_hook
    receptor_job = AWXReceptorJob(adoption_task, {'private_data_dir': private_data_dir})
    receptor_job.unit_id = unit_id
    receptor_job.stream_idle_timeout = settings.HADR_ADOPTION_STREAM_IDLE_TIMEOUT

    process_phase_failed = False
    res = None
    try:
        res = receptor_job._process_phase(receptor_ctl)  # blocks until unit completes
    except Exception:
        logger.exception(f'Adoption process phase failed for job {job.id} (unit={unit_id})')
        process_phase_failed = True

    if receptor_job.detached:
        # This controller is shutting down while the EE keeps running. The job stays 'running'
        # and the work unit stays alive, which is precisely what lets the next controller to
        # scan for orphans pick it up. Finalizing or releasing here would destroy that.
        logger.info(f'Job {job.id}: detached from unit {unit_id} during shutdown, leaving it for the next adopter')
        shutil.rmtree(private_data_dir, ignore_errors=True)
        return False

    if receptor_job.stream_stalled:
        # The unit finished and the execution node still holds the output; only the
        # transport between here and there is down. Deferring keeps the job 'running'
        # with its unit intact and the heartbeat re-queues it, so a later attempt can
        # stream the full event set rather than finalizing on a truncated one. Bounded
        # by the orphan age so a path that never recovers still converges.
        if not _adoption_stall_budget_exhausted(job):
            logger.info(f'Job {job.id}: results stream for unit {unit_id} stalled, deferring adoption for retry on next heartbeat')
            shutil.rmtree(private_data_dir, ignore_errors=True)
            return False

        # Budget spent. The work unit status is the only truthful source left: the
        # truncated stream reads as an error, which would record a job that actually
        # succeeded as failed and then release the unit holding the proof.
        logger.error(
            f'Job {job.id}: results stream for unit {unit_id} never recovered within '
            f'HADR_JOB_ADOPTION_TIMEOUT, finalizing from work unit status without full output'
        )
        callback.delay_update(job_explanation='Job output could not be retrieved from the execution node; final status was taken from the receptor work unit.')
        res = None
        process_phase_failed = True

    # Finalize status to DB first, then release the work unit — matching the ordering
    # in BaseTask.run() where release follows _finalize_job_run.
    # Keep private_data_dir available through finalization for post-run hooks.
    #
    # _process_phase -> _handle_work_error may return None for 'exceeded quota' where
    # the job is already set to 'pending' — don't finalize, let the next dispatch handle it.
    # _finalize_adoption_result returns False when adoption is deferred (unit still running) —
    # in that case, do NOT release the work unit.
    finalized = None
    try:
        failpoint('adoption.before_finalize', job_id=job.id)
        finalized = _finalize_adoption_result(job, callback, res, process_phase_failed, receptor_ctl, unit_id, private_data_dir)
    finally:
        # Release work unit based on finalization result:
        # - finalized=True: adoption succeeded, release unit
        # - finalized=False: adoption deferred (unit still running), don't release
        # - finalized=None: already handled (e.g., quota exceeded), release unit
        if finalized is not False:
            failpoint('adoption.after_finalize_before_release', job_id=job.id, finalized=finalized)
            receptor_job._receptor_release_work(receptor_ctl, getattr(res, 'status', 'error'))
        shutil.rmtree(private_data_dir, ignore_errors=True)

    return finalized if finalized is not None else True


def should_update_config(new_config):
    '''
    checks that the list of instances matches the list of
    tcp-peers in the config
    '''

    try:
        current_config = read_receptor_config()  # this gets receptor conf lock
    except FileNotFoundError:
        logger.warning("Receptor config file not found, config needs to be written.")
        return True
    for config_entry in current_config:
        if config_entry not in new_config:
            logger.warning(f"{config_entry} should not be in receptor config. Updating.")
            return True
    for config_entry in new_config:
        if config_entry not in current_config:
            logger.warning(f"{config_entry} missing from receptor config. Updating.")
            return True

    return False


def generate_config_data():
    # returns two values
    #   receptor config - based on current database peers
    #   should_update   - If True, receptor_config differs from the receptor conf file on disk
    addresses = ReceptorAddress.objects.filter(peers_from_control_nodes=True)

    receptor_config = list(RECEPTOR_CONFIG_STARTER)
    for address in addresses:
        if address.get_peer_type():
            peer = {
                f'{address.get_peer_type()}': {
                    'address': f'{address.get_full_address()}',
                    'tls': 'tlsclient',
                }
            }
            receptor_config.append(peer)
        else:
            logger.warning(f"Receptor address {address} has unsupported peer type, skipping.")
    should_update = should_update_config(receptor_config)
    return receptor_config, should_update


def reload_receptor():
    logger.warning("Receptor config changed, reloading receptor")

    # This needs to be outside of the lock because this function itself will acquire the lock.
    receptor_ctl = get_receptor_ctl()

    attempts = 10
    for backoff in range(1, attempts + 1):
        try:
            receptor_ctl.simple_command("reload")
            break
        except ValueError:
            logger.warning(f"Unable to reload Receptor configuration. {attempts - backoff} attempts left.")
            time.sleep(backoff)
    else:
        raise RuntimeError("Receptor reload failed")


@task(on_duplicate='queue_one')
def write_receptor_config():
    """
    This task runs async on each control node, K8S only.
    It is triggered whenever remote is added or removed, or if peers_from_control_nodes
    is flipped.
    It is possible for write_receptor_config to be called multiple times.
    For example, if new instances are added in quick succession.
    To prevent that case, each control node first grabs a DB advisory lock, specific
    to just that control node (i.e. multiple control nodes can run this function
    at the same time, since it only writes the local receptor config file)
    """
    with advisory_lock(f"{settings.CLUSTER_HOST_ID}_write_receptor_config", wait=True):
        # Config file needs to be updated
        receptor_config, should_update = generate_config_data()
        if should_update:
            lock = FileLock(__RECEPTOR_CONF_LOCKFILE)
            with lock:
                with open(__RECEPTOR_CONF, 'w') as file:
                    yaml.dump(receptor_config, file, default_flow_style=False)
            reload_receptor()


@task(queue=get_task_queuename, on_duplicate='discard')
def remove_deprovisioned_node(hostname):
    InstanceLink.objects.filter(source__hostname=hostname).update(link_state=InstanceLink.States.REMOVING)
    InstanceLink.objects.filter(target__instance__hostname=hostname).update(link_state=InstanceLink.States.REMOVING)

    node_jobs = UnifiedJob.objects.filter(
        execution_node=hostname,
        status__in=(
            'running',
            'waiting',
        ),
    )
    while node_jobs.exists():
        time.sleep(60)

    # This will as a side effect also delete the InstanceLinks that are tied to it.
    Instance.objects.filter(hostname=hostname).delete()
