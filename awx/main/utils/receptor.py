import logging
import yaml
import time

from receptorctl.socket_interface import ReceptorControl


logger = logging.getLogger('awx.main.utils.receptor')


def get_receptor_sockfile():
    receptor_conf = '/etc/receptor/receptor.conf'
    with open(receptor_conf, 'r') as f:
        data = yaml.safe_load(f)
    for section in data:
        for entry_name, entry_data in section.items():
            if entry_name == 'control-service':
                if 'filename' in entry_data:
                    return entry_data['filename']
                else:
                    raise RuntimeError(f'Receptor conf {receptor_conf} control-service entry does not have a filename parameter')
    else:
        raise RuntimeError(f'Receptor conf {receptor_conf} does not have control-service entry needed to get sockfile')


def get_receptor_ctl():
    receptor_sockfile = get_receptor_sockfile()
    return ReceptorControl(receptor_sockfile)


def worker_info(node_name, work_type='ansible-runner'):
    receptor_ctl = get_receptor_ctl()
    transmit_start = time.time()
    error_list = []
    data = {'errors': error_list, 'transmit_timing': 0.0}

    kwargs = {}
    if work_type != 'local':
        kwargs['ttl'] = '20s'
    result = receptor_ctl.submit_work(worktype=work_type, payload='', params={"params": f"--worker-info"}, node=node_name, **kwargs)

    unit_id = result['unitid']
    run_start = time.time()
    data['transmit_timing'] = run_start - transmit_start
    data['run_timing'] = 0.0

    try:

        resultfile = receptor_ctl.get_work_results(unit_id)

        stdout = ''

        while data['run_timing'] < 20.0:
            status = receptor_ctl.simple_command(f'work status {unit_id}')
            state_name = status.get('StateName')
            if state_name not in ('Pending', 'Running'):
                break
            data['run_timing'] = time.time() - run_start
            time.sleep(0.5)
        else:
            error_list.append(f'Timeout getting worker info on {node_name}, state remains in {state_name}')

        stdout = resultfile.read()
        stdout = str(stdout, encoding='utf-8')

    finally:

        res = receptor_ctl.simple_command(f"work release {unit_id}")
        if res != {'released': unit_id}:
            logger.warn(f'Could not confirm release of receptor work unit id {unit_id} from {node_name}, data: {res}')

        receptor_ctl.close()

    if state_name.lower() == 'failed':
        work_detail = status.get('Detail', '')
        if not work_detail.startswith('exit status'):
            error_list.append(f'Receptor error getting worker info from {node_name}, detail:\n{work_detail}')
        elif 'unrecognized arguments: --worker-info' in stdout:
            error_list.append(f'Old version (2.0.1 or earlier) of ansible-runner on node {node_name} without --worker-info')
        else:
            error_list.append(f'Unknown ansible-runner error on node {node_name}, stdout:\n{stdout}')
    else:
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

    # If we have a connection error, missing keys would be trivial consequence of that
    if not data['errors']:
        # see tasks.py usage of keys
        missing_keys = set(('runner_version', 'mem_in_bytes', 'cpu_count')) - set(data.keys())
        if missing_keys:
            data['errors'].append('Worker failed to return keys {}'.format(' '.join(missing_keys)))

    return data
