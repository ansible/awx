from unittest import mock

import pytest

from awx.main.models import SystemJob, SystemJobTemplate


@pytest.mark.django_db
class TestSystemJobTemplateLaunchValidation:
    """Tests for SystemJobTemplateLaunch.post input validation guard."""

    def test_launch_rejects_invalid_extra_vars(self, post, admin):
        """POST with non-integer days returns 400 BAD REQUEST."""
        sjt = SystemJobTemplate(name='test-sjt', job_type='cleanup_jobs')
        sjt.save()
        url = '/api/v2/system_job_templates/{}/launch/'.format(sjt.pk)
        response = post(
            url,
            {'extra_vars': {'days': 'not-a-number'}},
            user=admin,
        )
        assert response.status_code == 400

    @mock.patch(
        'awx.api.serializers.SystemJobSerializer.to_representation',
        return_value={},
    )
    @mock.patch.object(SystemJob, 'signal_start', return_value=None)
    def test_launch_accepts_valid_extra_vars(self, mock_signal, mock_repr, post, admin):
        """POST with valid integer days creates a system job (201)."""
        sjt = SystemJobTemplate(name='test-sjt', job_type='cleanup_jobs')
        sjt.save()
        url = '/api/v2/system_job_templates/{}/launch/'.format(sjt.pk)
        response = post(
            url,
            {'extra_vars': {'days': 30}},
            user=admin,
        )
        assert response.status_code == 201
        assert 'system_job' in response.data
