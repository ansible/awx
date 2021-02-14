from datetime import datetime
import json

from awxkit.utils import poll_until
from awxkit.exceptions import WaitUntilTimeout


def bytes_to_str(obj):
    try:
        return obj.decode()
    except AttributeError:
        return str(obj)


class HasStatus(object):

    completed_statuses = ['successful', 'failed', 'error', 'canceled']
    started_statuses = ['pending', 'running'] + completed_statuses

    @property
    def is_completed(self):
        return self.status.lower() in self.completed_statuses

    @property
    def is_successful(self):
        return self.status == 'successful'

    def wait_until_status(self, status, interval=1, timeout=60, **kwargs):
        status = [status] if not isinstance(status, (list, tuple)) else status
        try:
            poll_until(lambda: getattr(self.get(), 'status') in status, interval=interval, timeout=timeout, **kwargs)
        except WaitUntilTimeout:
            # This will raise a more informative error than just "WaitUntilTimeout" error
            self.assert_status(status)
        return self

    def wait_until_completed(self, interval=5, timeout=60, **kwargs):
        start_time = datetime.utcnow()
        HasStatus.wait_until_status(self, self.completed_statuses, interval=interval, timeout=timeout, **kwargs)
        if not getattr(self, 'event_processing_finished', True):
            elapsed = datetime.utcnow() - start_time
            time_left = timeout - elapsed.total_seconds()
            poll_until(lambda: getattr(self.get(), 'event_processing_finished', True),
                       interval=interval, timeout=time_left, **kwargs)
        return self

    def wait_until_started(self, interval=1, timeout=60):
        return self.wait_until_status(self.started_statuses, interval=interval, timeout=timeout)

    def failure_output_details(self):
        if getattr(self, 'result_stdout', ''):
            output = bytes_to_str(self.result_stdout)
            if output:
                return '\nstdout:\n{}'.format(output)
        return ''

    def assert_status(self, status_list, msg=None):
        if isinstance(status_list, str):
            status_list = [status_list]
        if self.status in status_list:
            # include corner cases in is_successful logic
            if 'successful' not in status_list or self.is_successful:
                return
        if msg is None:
            msg = ''
        else:
            msg += '\n'
        msg += '{0}-{1} has status of {2}, which is not in {3}.'.format(
            self.type.title(), self.id, self.status, status_list
        )
        if getattr(self, 'job_explanation', ''):
            msg += '\njob_explanation: {}'.format(bytes_to_str(self.job_explanation))
        if getattr(self, 'result_traceback', ''):
            msg += '\nresult_traceback:\n{}'.format(bytes_to_str(self.result_traceback))

        msg += self.failure_output_details()

        if getattr(self, 'job_explanation', '').startswith('Previous Task Failed'):
            try:
                data = json.loads(self.job_explanation.replace('Previous Task Failed: ', ''))
                dep_output = self.connection.get(
                    '{0}/api/v2/{1}s/{2}/stdout/'.format(
                        self.endpoint.split('/api')[0], data['job_type'], data['job_id']
                    ),
                    query_parameters=dict(format='txt_download')
                ).content
                msg += '\nDependency output:\n{}'.format(bytes_to_str(dep_output))
            except Exception as e:
                msg += '\nFailed to obtain dependency stdout: {}'.format(e)

        msg += '\nTIME WHEN STATUS WAS FOUND: {} (UTC)\n'.format(datetime.utcnow())

        raise AssertionError(msg)

    def assert_successful(self, msg=None):
        return self.assert_status('successful', msg=msg)
