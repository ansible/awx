# Python
import pytest
import mock

# AWX
from awx.api.serializers import (
    JobTemplateSerializer,
)
from awx.main.models import (
    Job,
)

#DRF
from rest_framework import serializers

def mock_JT_resource_data():
    return ({}, [])

@pytest.fixture
def job_template(mocker):
    mock_jt = mocker.MagicMock(pk=5)
    mock_jt.resource_validation_data = mock_JT_resource_data
    return mock_jt

@pytest.fixture
def job(mocker, job_template):
    return mocker.MagicMock(pk=5, job_template=job_template)

@pytest.fixture
def jobs(mocker):
    return [Job(id=x, name='job-%d' % x) for x in xrange(0, 25)]

@mock.patch('awx.api.serializers.UnifiedJobTemplateSerializer.get_related', lambda x,y: {})
@mock.patch('awx.api.serializers.JobOptionsSerializer.get_related', lambda x,y: {})
class TestJobTemplateSerializerGetRelated():
    @pytest.mark.parametrize("related_resource_name", [
        'jobs',
        'schedules',
        'activity_stream',
        'launch',
        'notification_templates_any',
        'notification_templates_success',
        'notification_templates_error',
        'survey_spec',
        'labels',
        'callback',
    ])
    def test_get_related(self, test_get_related, job_template, related_resource_name):
        test_get_related(JobTemplateSerializer, job_template, 'job_templates', related_resource_name)

    def test_callback_absent(self, get_related_mock_and_run, job_template):
        job_template.host_config_key = None
        related = get_related_mock_and_run(JobTemplateSerializer, job_template)
        assert 'callback' not in related

class TestJobTemplateSerializerGetSummaryFields():
    def test__recent_jobs(self, mocker, job_template, jobs):

        job_template.jobs.all = mocker.MagicMock(**{'order_by.return_value': jobs})
        job_template.jobs.all.return_value = job_template.jobs.all

        serializer = JobTemplateSerializer()
        recent_jobs = serializer._recent_jobs(job_template)

        job_template.jobs.all.assert_called_once_with()
        job_template.jobs.all.order_by.assert_called_once_with('-created')
        assert len(recent_jobs) == 10
        for x in jobs[:10]:
            assert recent_jobs == [{'id': x.id, 'status': x.status, 'finished': x.finished} for x in jobs[:10]]

    def test_survey_spec_exists(self, test_get_summary_fields, mocker, job_template):
        job_template.survey_spec = {'name': 'blah', 'description': 'blah blah'}
        test_get_summary_fields(JobTemplateSerializer, job_template, 'survey')

    def test_survey_spec_absent(self, get_summary_fields_mock_and_run, job_template):
        job_template.survey_spec = None
        summary = get_summary_fields_mock_and_run(JobTemplateSerializer, job_template)
        assert 'survey' not in summary

    @pytest.mark.skip(reason="RBAC needs to land")
    def test_can_copy_true(self, mocker, job_template):
        pass

    @pytest.mark.skip(reason="RBAC needs to land")
    def test_can_copy_false(self, mocker, job_template):
        pass

    @pytest.mark.skip(reason="RBAC needs to land")
    def test_can_edit_true(self, mocker, job_template):
        pass

    @pytest.mark.skip(reason="RBAC needs to land")
    def test_can_edit_false(self, mocker, job_template):
        pass

class TestJobTemplateSerializerValidation(object):

    good_extra_vars = ["{\"test\": \"keys\"}", "---\ntest: key"]
    bad_extra_vars = ["{\"test\": \"keys\"", "---\ntest: [2"]

    def test_validate_extra_vars(self):
        serializer = JobTemplateSerializer()
        for ev in self.good_extra_vars:
            serializer.validate_extra_vars(ev)
        for ev in self.bad_extra_vars:
            with pytest.raises(serializers.ValidationError):
                serializer.validate_extra_vars(ev)

