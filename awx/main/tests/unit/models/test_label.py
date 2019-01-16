import pytest
from unittest import mock

from awx.main.models.label import Label
from awx.main.models.unified_jobs import UnifiedJobTemplate, UnifiedJob


mock_query_set = mock.MagicMock()

mock_objects = mock.MagicMock(filter=mock.MagicMock(return_value=mock_query_set))


@mock.patch('awx.main.models.label.Label.objects', mock_objects)
class TestLabelFilterMocked:
    def test_get_orphaned_labels(self, mocker):
        ret = Label.get_orphaned_labels()

        assert mock_query_set == ret
        Label.objects.filter.assert_called_with(organization=None, unifiedjobtemplate_labels__isnull=True)

    def test_is_detached(self, mocker):
        mock_query_set.count.return_value = 1

        label = Label(id=37)
        ret = label.is_detached()

        assert ret is True
        Label.objects.filter.assert_called_with(id=37, unifiedjob_labels__isnull=True, unifiedjobtemplate_labels__isnull=True)
        mock_query_set.count.assert_called_with()

    def test_is_detached_not(self, mocker):
        mock_query_set.count.return_value = 0

        label = Label(id=37)
        ret = label.is_detached()

        assert ret is False
        Label.objects.filter.assert_called_with(id=37, unifiedjob_labels__isnull=True, unifiedjobtemplate_labels__isnull=True)
        mock_query_set.count.assert_called_with()

    @pytest.mark.parametrize("jt_count,j_count,expected", [
        (1, 0, True),
        (0, 1, True),
        (1, 1, False),
    ])
    def test_is_candidate_for_detach(self, mocker, jt_count, j_count, expected):
        mock_job_qs = mocker.MagicMock()
        mock_job_qs.count = mocker.MagicMock(return_value=j_count)
        mocker.patch.object(UnifiedJob, 'objects', mocker.MagicMock(
            filter=mocker.MagicMock(return_value=mock_job_qs)))

        mock_jt_qs = mocker.MagicMock()
        mock_jt_qs.count = mocker.MagicMock(return_value=jt_count)
        mocker.patch.object(UnifiedJobTemplate, 'objects', mocker.MagicMock(
            filter=mocker.MagicMock(return_value=mock_jt_qs)))

        label = Label(id=37)
        ret = label.is_candidate_for_detach()

        UnifiedJob.objects.filter.assert_called_with(labels__in=[label.id])
        UnifiedJobTemplate.objects.filter.assert_called_with(labels__in=[label.id])
        mock_job_qs.count.assert_called_with()
        mock_jt_qs.count.assert_called_with()

        assert ret is expected
