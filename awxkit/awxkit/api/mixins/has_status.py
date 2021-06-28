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
            poll_until(lambda: getattr(self.get(), 'event_processing_finished', True), interval=interval, timeout=time_left, **kwargs)
        return self

    def wait_until_started(self, interval=1, timeout=60):
        return self.wait_until_status(self.started_statuses, interval=interval, timeout=timeout)

    def failure_output_details(self):
        msg = ''
        if getattr(self, 'result_stdout', ''):
            output = bytes_to_str(self.result_stdout)
            if output:
                msg = '\nstdout:\n{}'.format(output)
        if getattr(self, 'job_explanation', ''):
            msg += '\njob_explanation: {}'.format(bytes_to_str(self.job_explanation))
        if getattr(self, 'result_traceback', ''):
            msg += '\nresult_traceback:\n{}'.format(bytes_to_str(self.result_traceback))
        return msg

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
        msg += '{0}-{1} has status of {2}, which is not in {3}.'.format(self.type.title(), self.id, self.status, status_list)
        if getattr(self, 'execution_environment', ''):
            msg += '\nexecution_environment: {}'.format(bytes_to_str(self.execution_environment))
            if getattr(self, 'related', False):
                ee = self.related.execution_environment.get()
                msg += f'\nee_image: {ee.image}'
                msg += f'\nee_credential: {ee.credential}'
                msg += f'\nee_pull_option: {ee.pull}'
                msg += f'\nee_summary_fields: {ee.summary_fields}'

        msg += self.failure_output_details()

        if getattr(self, 'job_explanation', '').startswith('Previous Task Failed'):
            try:
                data = json.loads(self.job_explanation.replace('Previous Task Failed: ', ''))
                dependency = self.walk('/api/v2/{0}s/{1}/'.format(data['job_type'], data['job_id']))
                if hasattr(dependency, 'failure_output_details'):
                    msg += '\nDependency output:\n{}'.format(dependency.failure_output_details())
                else:
                    msg += '\nDependency info:\n{}'.format(dependency)
            except Exception as e:
                msg += '\nFailed to obtain dependency stdout: {}'.format(e)

        msg += '\nTIME WHEN STATUS WAS FOUND: {} (UTC)\n'.format(datetime.utcnow())

        raise AssertionError(msg)

    def assert_successful(self, msg=None):
        return self.assert_status('successful', msg=msg)
