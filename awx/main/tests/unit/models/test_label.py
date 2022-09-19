import pytest
from unittest import mock

from awx.main.models import (
    Label,
    UnifiedJobTemplate,
    UnifiedJob,
    Inventory,
    Schedule,
    WorkflowJobTemplateNode,
    WorkflowJobNode,
)


mock_query_set = mock.MagicMock()

mock_objects = mock.MagicMock(filter=mock.MagicMock(return_value=mock_query_set))


@pytest.mark.django_db
@mock.patch('awx.main.models.label.Label.objects', mock_objects)
class TestLabelFilterMocked:
    def test_is_detached(self, mocker):
        mock_query_set.exists.return_value = True

        label = Label(id=37)
        ret = label.is_detached()

        assert ret is True
        Label.objects.filter.assert_called_with(
            id=37,
            unifiedjob_labels__isnull=True,
            unifiedjobtemplate_labels__isnull=True,
            inventory_labels__isnull=True,
            schedule_labels__isnull=True,
            workflowjobtemplatenode_labels__isnull=True,
            workflowjobnode_labels__isnull=True,
        )
        mock_query_set.exists.assert_called_with()

    def test_is_detached_not(self, mocker):
        mock_query_set.exists.return_value = False

        label = Label(id=37)
        ret = label.is_detached()

        assert ret is False
        Label.objects.filter.assert_called_with(
            id=37,
            unifiedjob_labels__isnull=True,
            unifiedjobtemplate_labels__isnull=True,
            inventory_labels__isnull=True,
            schedule_labels__isnull=True,
            workflowjobtemplatenode_labels__isnull=True,
            workflowjobnode_labels__isnull=True,
        )

        mock_query_set.exists.assert_called_with()

    @pytest.mark.parametrize(
        "jt_count,j_count,inv_count,sched_count,wfnode_count,wfnodej_count,expected",
        [
            (1, 0, 0, 0, 0, 0, True),
            (0, 1, 0, 0, 0, 0, True),
            (1, 1, 0, 0, 0, 0, False),
            (0, 0, 1, 0, 0, 0, True),
            (1, 0, 1, 0, 0, 0, False),
            (0, 1, 1, 0, 0, 0, False),
            (1, 1, 1, 0, 0, 0, False),
            (0, 0, 0, 1, 0, 0, True),
            (1, 0, 0, 1, 0, 0, False),
            (0, 1, 0, 1, 0, 0, False),
            (1, 1, 0, 1, 0, 0, False),
            (0, 0, 1, 1, 0, 0, False),
            (1, 0, 1, 1, 0, 0, False),
            (0, 1, 1, 1, 0, 0, False),
            (1, 1, 1, 1, 0, 0, False),
            (0, 0, 0, 0, 1, 0, True),
            (1, 0, 0, 0, 1, 0, False),
            (0, 1, 0, 0, 1, 0, False),
            (1, 1, 0, 0, 1, 0, False),
            (0, 0, 1, 0, 1, 0, False),
            (1, 0, 1, 0, 1, 0, False),
            (0, 1, 1, 0, 1, 0, False),
            (1, 1, 1, 0, 1, 0, False),
            (0, 0, 0, 1, 1, 0, False),
            (1, 0, 0, 1, 1, 0, False),
            (0, 1, 0, 1, 1, 0, False),
            (1, 1, 0, 1, 1, 0, False),
            (0, 0, 1, 1, 1, 0, False),
            (1, 0, 1, 1, 1, 0, False),
            (0, 1, 1, 1, 1, 0, False),
            (1, 1, 1, 1, 1, 0, False),
            (0, 0, 0, 0, 0, 1, True),
            (1, 0, 0, 0, 0, 1, False),
            (0, 1, 0, 0, 0, 1, False),
            (1, 1, 0, 0, 0, 1, False),
            (0, 0, 1, 0, 0, 1, False),
            (1, 0, 1, 0, 0, 1, False),
            (0, 1, 1, 0, 0, 1, False),
            (1, 1, 1, 0, 0, 1, False),
            (0, 0, 0, 1, 0, 1, False),
            (1, 0, 0, 1, 0, 1, False),
            (0, 1, 0, 1, 0, 1, False),
            (1, 1, 0, 1, 0, 1, False),
            (0, 0, 1, 1, 0, 1, False),
            (1, 0, 1, 1, 0, 1, False),
            (0, 1, 1, 1, 0, 1, False),
            (1, 1, 1, 1, 0, 1, False),
            (0, 0, 0, 0, 1, 1, False),
            (1, 0, 0, 0, 1, 1, False),
            (0, 1, 0, 0, 1, 1, False),
            (1, 1, 0, 0, 1, 1, False),
            (0, 0, 1, 0, 1, 1, False),
            (1, 0, 1, 0, 1, 1, False),
            (0, 1, 1, 0, 1, 1, False),
            (1, 1, 1, 0, 1, 1, False),
            (0, 0, 0, 1, 1, 1, False),
            (1, 0, 0, 1, 1, 1, False),
            (0, 1, 0, 1, 1, 1, False),
            (1, 1, 0, 1, 1, 1, False),
            (0, 0, 1, 1, 1, 1, False),
            (1, 0, 1, 1, 1, 1, False),
            (0, 1, 1, 1, 1, 1, False),
            (1, 1, 1, 1, 1, 1, False),
        ],
    )
    def test_is_candidate_for_detach(self, mocker, jt_count, j_count, inv_count, sched_count, wfnode_count, wfnodej_count, expected):
        counts = [jt_count, j_count, inv_count, sched_count, wfnode_count, wfnodej_count]
        models = [UnifiedJobTemplate, UnifiedJob, Inventory, Schedule, WorkflowJobTemplateNode, WorkflowJobNode]
        mockers = []
        for index in range(0, len(models)):
            a_mocker = mocker.MagicMock()
            a_mocker.count = mocker.MagicMock(return_value=counts[index])
            mocker.patch.object(models[index], 'objects', mocker.MagicMock(filter=mocker.MagicMock(return_value=a_mocker)))
            mockers.append(a_mocker)

        label = Label(id=37)
        ret = label.is_candidate_for_detach()

        for index in range(0, len(models)):
            models[index].objects.filter.assert_called_with(labels__in=[label.id])
        for index in range(0, len(mockers)):
            mockers[index].count.assert_called_with()

        assert ret is expected
