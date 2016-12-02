from awx.main.utils import format_for_log
import datetime

# Example data
event_data = {
    'stdout': u'\x1b[0;36mskipping: [host1]\x1b[0m\r\n', u'uuid': u'ffe4858c-ac38-4cab-9192-b07bdbe80502',
    u'created': datetime.datetime(2016, 11, 10, 14, 59, 16, 376051), 'counter': 17, u'job_id': 209,
    u'event': u'runner_on_skipped', 'parent_id': 1937, 'end_line': 24, 'start_line': 23,
    u'event_data': {
        u'play_pattern': u'all', u'play': u'all', u'task': u'Scan files (Windows)',
        u'task_args': u'paths={{ scan_file_paths }}, recursive={{ scan_use_recursive }}, get_checksum={{ scan_use_checksum }}',
        u'remote_addr': u'host1', u'pid': 1427, u'play_uuid': u'da784361-3811-4ea7-9cc8-46ec758fde66',
        u'task_uuid': u'4f9525fd-bc25-4ace-9eb2-adad9fa21a94', u'event_loop': None,
        u'playbook_uuid': u'653fd95e-f718-428e-9df0-3f279df9f07e', u'playbook': u'scan_facts.yml',
        u'task_action': u'win_scan_files', u'host': u'host1', u'task_path': None}}

event_stats = {
    'stdout': u'asdf', u'created': datetime.datetime(2016, 11, 10, 14, 59, 16, 385416),
    'counter': 18, u'job_id': 209, u'event': u'playbook_on_stats', 'parent_id': 1923,
    'end_line': 28, 'start_line': 24, u'event_data': {
        u'skipped': {u'host1': 4}, u'ok': {u'host2': 3}, u'changed': {}, 
        u'pid': 1427, u'dark': {}, u'playbook_uuid': u'653fd95e-f718-428e-9df0-3f279df9f07e', 
        u'playbook': u'scan_facts.yml', u'failures': {}, u'processed': {u'duck': 1}
    }
}



def test_format_event():
    log_data = format_for_log(event_data, kind='event')
    assert log_data['event_host'] == 'host1'

