
from awx.main.models import Job, JobEvent

from awx.main.utils.formatters import LogstashFormatter


def test_log_from_job_event_object():
    job = Job(id=4)
    event = JobEvent(job_id=job.id)
    formatter = LogstashFormatter()

    data_for_log = formatter.reformat_data_for_log(
        dict(python_objects=dict(job_event=event)), kind='job_events')

    # Check entire body of data for any exceptions from getattr on event object
    for fd in data_for_log:
        if not isinstance(data_for_log[fd], str):
            continue
        assert 'Exception' not in data_for_log[fd], 'Exception delivered in data: {}'.format(data_for_log[fd])

    # Verify existence of certain high-importance fields
    for fd in ['changed', 'uuid', 'start_line', 'end_line', 'id', 'counter', 'host_name', 'stdout']:
        assert fd in data_for_log

    assert data_for_log['job'] == 4
