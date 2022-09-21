# Python
import pytest
from unittest import mock
import json

# AWX
from awx.api.serializers import JobSerializer, JobOptionsSerializer

from awx.main.models import (
    Label,
    Job,
    JobEvent,
    ProjectUpdateEvent,
)


def mock_JT_resource_data():
    return {}


@pytest.fixture
def job_template(mocker):
    mock_jt = mocker.MagicMock(pk=5)
    mock_jt.validation_errors = mock_JT_resource_data
    return mock_jt


@pytest.fixture
def project_update(mocker):
    mock_pu = mocker.MagicMock(pk=1)
    return mock_pu


@pytest.fixture
def job(mocker, job_template, project_update):
    return mocker.MagicMock(pk=5, job_template=job_template, project_update=project_update, workflow_job_id=None, execution_environment_id=None)


@pytest.fixture
def labels(mocker):
    return [Label(id=x, name='label-%d' % x) for x in range(0, 25)]


@pytest.fixture
def jobs(mocker):
    return [Job(id=x, name='job-%d' % x) for x in range(0, 25)]


@mock.patch('awx.api.serializers.UnifiedJobTemplateSerializer.get_related', lambda x, y: {})
@mock.patch('awx.api.serializers.JobOptionsSerializer.get_related', lambda x, y: {})
class TestJobSerializerGetRelated:
    @pytest.mark.parametrize(
        "related_resource_name",
        [
            'job_events',
            'relaunch',
            'labels',
        ],
    )
    def test_get_related(self, test_get_related, job, related_resource_name):
        test_get_related(JobSerializer, job, 'jobs', related_resource_name)

    def test_job_template_absent(self, job):
        job.job_template = None
        serializer = JobSerializer()
        related = serializer.get_related(job)
        assert 'job_template' not in related

    def test_job_template_present(self, get_related_mock_and_run, job):
        related = get_related_mock_and_run(JobSerializer, job)
        assert 'job_template' in related
        assert related['job_template'] == '/api/v2/%s/%d/' % ('job_templates', job.job_template.pk)


@mock.patch('awx.api.serializers.BaseSerializer.to_representation', lambda self, obj: {'extra_vars': obj.extra_vars})
class TestJobSerializerSubstitution:
    def test_survey_password_hide(self, mocker):
        job = mocker.MagicMock(
            **{'display_extra_vars.return_value': '{\"secret_key\": \"$encrypted$\"}', 'extra_vars.return_value': '{\"secret_key\": \"my_password\"}'}
        )
        serializer = JobSerializer(job)
        rep = serializer.to_representation(job)
        extra_vars = json.loads(rep['extra_vars'])
        assert extra_vars['secret_key'] == '$encrypted$'
        job.display_extra_vars.assert_called_once_with()
        assert 'my_password' not in extra_vars


@mock.patch('awx.api.serializers.BaseSerializer.get_summary_fields', lambda x, y: {})
class TestJobOptionsSerializerGetSummaryFields:
    def test__summary_field_labels_10_max(self, mocker, job_template, labels):
        job_template.labels.all = mocker.MagicMock(**{'return_value': labels})

        serializer = JobOptionsSerializer()
        summary_labels = serializer._summary_field_labels(job_template)

        assert len(summary_labels['results']) == 10
        assert summary_labels['results'] == [{'id': x.id, 'name': x.name} for x in labels[:10]]

    def test_labels_exists(self, test_get_summary_fields, job_template):
        test_get_summary_fields(JobOptionsSerializer, job_template, 'labels')


class TestJobDetailSerializerGetHostStatusCountFields(object):
    def test_hosts_are_counted_once(self):
        mock_event = JobEvent(
            **{
                'event': 'playbook_on_stats',
                'event_data': {
                    'skipped': {
                        'localhost': 2,
                        'fiz': 1,
                    },
                    'ok': {
                        'localhost': 1,
                        'foo': 2,
                    },
                    'changed': {
                        'localhost': 1,
                        'bar': 3,
                    },
                    'dark': {
                        'localhost': 2,
                        'fiz': 2,
                    },
                },
            }
        )

        assert mock_event.get_host_status_counts() == {'ok': 1, 'changed': 1, 'dark': 2}


class TestProjectUpdateDetailSerializerGetHostStatusCountFields(object):
    def test_hosts_are_counted_once(self):
        mock_event = ProjectUpdateEvent(
            **{
                'event': 'playbook_on_stats',
                'event_data': {
                    'skipped': {
                        'localhost': 2,
                        'fiz': 1,
                    },
                    'ok': {
                        'localhost': 1,
                        'foo': 2,
                    },
                    'changed': {
                        'localhost': 1,
                        'bar': 3,
                    },
                    'dark': {
                        'localhost': 2,
                        'fiz': 2,
                    },
                },
            }
        )

        assert mock_event.get_host_status_counts() == {'ok': 1, 'changed': 1, 'dark': 2}
