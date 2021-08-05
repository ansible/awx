import logging
import yaml

from receptorctl.socket_interface import ReceptorControl


logger = logging.getLogger('awx.main.utils.receptor')


def get_receptor_ctl():
    return ReceptorControl('/var/run/receptor/receptor.sock')


def worker_info(node_name):
    receptor_ctl = get_receptor_ctl()

    result = receptor_ctl.submit_work(worktype='ansible-runner', payload='', params={"params": f"--worker-info"}, ttl='20s', node=node_name)

    unit_id = result['unitid']

    resultfile = receptor_ctl.get_work_results(unit_id)

    stdout = ''

    while True:
        line = resultfile.readline()
        if line:
            stdout += str(line, encoding='utf-8').strip()
        else:
            status = receptor_ctl.simple_command(f'work status {unit_id}')
            state_name = status.get('StateName')
            if state_name != 'Running':
                break

    data = {}

    if state_name.lower() == 'failed':
        work_detail = status.get('Detail', '')
        if not work_detail.startswith('exit status'):
            logger.info(f'Mesh-level error getting worker info from {node_name}, detail:\n{work_detail}')
        elif 'unrecognized arguments: --worker-info' in stdout:
            # 2.0.1 is the last version before --worker-info was introduced
            logger.info(f'Old version of ansible-runner on node {node_name} without --worker-info')
        else:
            logger.warn(f'Unknown ansible-runner error on node {node_name}, stdout:\n{stdout}')
    else:
        yaml_stdout = stdout.strip()
        try:
            data = yaml.safe_load(yaml_stdout)
        except Exception as json_e:
            logger.warn(f'Failed to parse node {node_name} worker info output as YAML, error: {json_e}, data:\n{yaml_stdout}')

    res = receptor_ctl.simple_command(f"work release {unit_id}")
    if res != {'released': unit_id}:
        logger.warn(f'Could not confirm release of receptor work unit id {unit_id}, data: {res}')

    return data
