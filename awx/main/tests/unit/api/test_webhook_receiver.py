from unittest import mock

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from awx.api.views.webhooks import BitbucketDcWebhookReceiver


class TestBitbucketDcDiagnosticsPingGuard:
    """
    Regression: unauthenticated diagnostics:ping must return 200
    immediately WITHOUT calling get_object(), so the response is
    identical whether or not the targeted template exists -- closing
    the 200-vs-403 enumeration oracle.
    """

    @staticmethod
    def _post(event_key):
        factory = APIRequestFactory()
        return factory.post(
            '/api/v2/workflow_job_templates/1/bitbucket_dc/',
            data={},
            format='json',
            HTTP_X_EVENT_KEY=event_key,
        )

    def test_diagnostics_ping_returns_200_without_calling_get_object(self):
        """Guard fires: diagnostics:ping returns 200 and never touches
        get_object, so no information about the template leaks."""
        request = self._post('diagnostics:ping')
        view = BitbucketDcWebhookReceiver.as_view()

        with mock.patch.object(
            BitbucketDcWebhookReceiver,
            'get_object',
        ) as mock_get_obj:
            response = view(
                request,
                model_kwarg='workflow_job_templates',
                pk=99999,
            )

        assert response.status_code == status.HTTP_200_OK
        mock_get_obj.assert_not_called()

    def test_recognized_event_still_calls_get_object(self):
        """Guard does NOT fire for real events: repo:refs_changed proceeds
        to get_object (and would continue to signature validation)."""
        request = self._post('repo:refs_changed')
        view = BitbucketDcWebhookReceiver.as_view()

        with mock.patch.object(
            BitbucketDcWebhookReceiver,
            'get_object',
            side_effect=PermissionDenied,
        ) as mock_get_obj:
            response = view(
                request,
                model_kwarg='workflow_job_templates',
                pk=99999,
            )

        mock_get_obj.assert_called_once()
        assert response.status_code == status.HTTP_403_FORBIDDEN
