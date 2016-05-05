# Python
import pytest
import mock

# AWX
from awx.api.serializers import JobTemplateSerializer, JobSerializer, JobOptionsSerializer
from awx.main.models import Label, Job

#DRF
from rest_framework import serializers

@pytest.fixture
def job_template(mocker):
    return mocker.MagicMock(pk=5)

@pytest.fixture
def job(mocker, job_template):
    return mocker.MagicMock(pk=5, job_template=job_template)

@pytest.fixture
def labels(mocker):
    return [Label(id=x, name='label-%d' % x) for x in xrange(0, 25)]

@pytest.fixture
def jobs(mocker):
    return [Job(id=x, name='job-%d' % x) for x in xrange(0, 25)]

class GetRelatedMixin:
    def _assert(self, model_obj, related, resource_name, related_resource_name):
        assert related_resource_name in related
        assert related[related_resource_name] == '/api/v1/%s/%d/%s/' % (resource_name, model_obj.pk, related_resource_name)

    def _mock_and_run(self, serializer_class, model_obj):
        serializer = serializer_class()
        related = serializer.get_related(model_obj)
        return related

    def _test_get_related(self, serializer_class, model_obj, resource_name, related_resource_name):
        related = self._mock_and_run(serializer_class, model_obj)
        self._assert(model_obj, related, resource_name, related_resource_name)
        return related

class GetSummaryFieldsMixin:
    def _assert(self, summary, summary_field_name):
        assert summary_field_name in summary

    def _mock_and_run(self, serializer_class, model_obj):
        serializer = serializer_class()
        return serializer.get_summary_fields(model_obj)

    def _test_get_summary_fields(self, serializer_class, model_obj, summary_field_name):
        summary = self._mock_and_run(serializer_class, model_obj)
        self._assert(summary, summary_field_name)
        return summary

@mock.patch('awx.api.serializers.UnifiedJobTemplateSerializer.get_related', lambda x,y: {})
@mock.patch('awx.api.serializers.JobOptionsSerializer.get_related', lambda x,y: {})
class TestJobTemplateSerializerGetRelated(GetRelatedMixin):
    @pytest.mark.parametrize("related_resource_name", [
        'jobs',
        'schedules',
        'activity_stream',
        'launch',
        'notifiers_any',
        'notifiers_success',
        'notifiers_error',
        'survey_spec',
        'labels',
        'callback',
    ])
    def test_get_related(self, job_template, related_resource_name):
        self._test_get_related(JobTemplateSerializer, job_template, 'job_templates', related_resource_name)

    def test_callback_absent(self, job_template):
        job_template.host_config_key = None
        related = self._mock_and_run(JobTemplateSerializer, job_template)
        assert 'callback' not in related

class TestJobTemplateSerializerGetSummaryFields(GetSummaryFieldsMixin):
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

    def test_survey_spec_exists(self, mocker, job_template):
        job_template.survey_spec = {'name': 'blah', 'description': 'blah blah'}
        self._test_get_summary_fields(JobTemplateSerializer, job_template, 'survey')

    def test_survey_spec_absent(self, mocker, job_template):
        job_template.survey_spec = None
        summary = self._mock_and_run(JobTemplateSerializer, job_template)
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

@mock.patch('awx.api.serializers.UnifiedJobTemplateSerializer.get_related', lambda x,y: {})
@mock.patch('awx.api.serializers.JobOptionsSerializer.get_related', lambda x,y: {})
class TestJobSerializerGetRelated(GetRelatedMixin):
    @pytest.mark.parametrize("related_resource_name", [
        'job_events', 
        'job_plays', 
        'job_tasks', 
        'relaunch', 
        'labels', 
    ])
    def test_get_related(self, mocker, job, related_resource_name):
        self._test_get_related(JobSerializer, job, 'jobs', related_resource_name)

    def test_job_template_absent(self, mocker, job):
        job.job_template = None
        serializer = JobSerializer()
        related = serializer.get_related(job)
        assert 'job_template' not in related

    def test_job_template_present(self, job):
        related = self._mock_and_run(JobSerializer, job)
        assert 'job_template' in related
        assert related['job_template'] == '/api/v1/%s/%d/' % ('job_templates', job.job_template.pk)

@mock.patch('awx.api.serializers.BaseSerializer.get_summary_fields', lambda x,y: {})
class TestJobOptionsSerializerGetSummaryFields(GetSummaryFieldsMixin):
    def test__summary_field_labels_10_max(self, mocker, job_template, labels):
        job_template.labels.all = mocker.MagicMock(**{'order_by.return_value': labels})
        job_template.labels.all.return_value = job_template.labels.all

        serializer = JobOptionsSerializer()
        summary_labels = serializer._summary_field_labels(job_template)

        job_template.labels.all.order_by.assert_called_with('name')
        assert len(summary_labels) == 10
        assert summary_labels == [{'id': x.id, 'name': x.name} for x in labels[:10]]

    def test_labels_exists(self, mocker, job_template):
        self._test_get_summary_fields(JobOptionsSerializer, job_template, 'labels')

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
