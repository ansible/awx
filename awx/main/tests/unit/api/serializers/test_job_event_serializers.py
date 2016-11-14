import pytest
import mock

from awx.api.serializers import JobEventSerializer
from awx.main.models import (
    Job,
    JobTemplate,
    JobEvent,
)


@pytest.fixture
def job_event(mocker):
    job_event = mocker.MagicMock(spec=JobEvent)

    job = Job(id=1, name="job-1")
    job.job_template = JobTemplate(id=1, name="job-template-1")
    job_event.job = job

    return job_event


def test_summary_field_workflow_exists(job_event):
    with mock.patch('awx.api.serializers.BaseSerializer.get_summary_fields', lambda x,y: {'job':{}}):
        serializer = JobEventSerializer(job_event)
        summary_fields = serializer.get_summary_fields(job_event)
        assert 'spawned_by_workflow' in summary_fields['job']
        assert 'workflow_job_id' in summary_fields['job']
