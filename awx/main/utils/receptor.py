import logging
import yaml
import time
from enum import Enum, unique

from receptorctl.socket_interface import ReceptorControl

from awx.main.exceptions import ReceptorNodeNotFound

from django.conf import settings


logger = logging.getLogger('awx.main.utils.receptor')

__RECEPTOR_CONF = '/etc/receptor/receptor.conf'

RECEPTOR_ACTIVE_STATES = ('Pending', 'Running')


@unique
class ReceptorConnectionType(Enum):
    DATAGRAM = 0
    STREAM = 1
    STREAMTLS = 2


def get_receptor_sockfile():
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


def get_conn_type(node_name, receptor_ctl):
    all_nodes = receptor_ctl.simple_command("status").get('Advertisements', None)
    for node in all_nodes:
        if node.get('NodeID') == node_name:
            return ReceptorConnectionType(node.get('ConnType'))
    raise ReceptorNodeNotFound(f'Instance {node_name} is not in the receptor mesh')


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
        if (extra_data is None) or (extra_data.get('RemoteWorkType') != 'ansible-runner'):
            continue  # if this is not ansible-runner work, we do not want to touch it
        params = extra_data.get('RemoteParams', {}).get('params')
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
                logger.warn(f'Could not confirm release of receptor work unit id {unit_id} from {node}, data: {res}')

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

    except ReceptorNodeNotFound as exc:
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
