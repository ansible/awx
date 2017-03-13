import pytest
import mock
from awx.main.models import (
    UnifiedJob,
    InventoryUpdate,
    Job,
)


@pytest.fixture
def dependent_job(mocker):
    j = Job(id=3, name='I_am_a_job')
    j.cancel = mocker.MagicMock(return_value=True)
    return [j]


def test_cancel(mocker, dependent_job):
    with mock.patch.object(UnifiedJob, 'cancel', return_value=True) as parent_cancel:
        iu = InventoryUpdate()

        iu.get_dependent_jobs = mocker.MagicMock(return_value=dependent_job)
        iu.save = mocker.MagicMock()
        build_job_explanation_mock = mocker.MagicMock()
        iu._build_job_explanation = mocker.MagicMock(return_value=build_job_explanation_mock)

        iu.cancel()

        parent_cancel.assert_called_with(job_explanation=None)
        dependent_job[0].cancel.assert_called_with(job_explanation=build_job_explanation_mock)
        

def test__build_job_explanation():
    iu = InventoryUpdate(id=3, name='I_am_an_Inventory_Update')

    job_explanation = iu._build_job_explanation()

    assert job_explanation == 'Previous Task Canceled: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % \
                              ('inventory_update', 'I_am_an_Inventory_Update', 3)
