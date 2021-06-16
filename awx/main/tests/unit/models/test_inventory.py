import pytest
from unittest import mock

from django.core.exceptions import ValidationError

from awx.main.models import (
    UnifiedJob,
    InventoryUpdate,
    InventorySource,
)


def test_cancel(mocker):
    with mock.patch.object(UnifiedJob, 'cancel', return_value=True) as parent_cancel:
        iu = InventoryUpdate()

        iu.save = mocker.MagicMock()
        build_job_explanation_mock = mocker.MagicMock()
        iu._build_job_explanation = mocker.MagicMock(return_value=build_job_explanation_mock)

        iu.cancel()

        parent_cancel.assert_called_with(is_chain=False, job_explanation=None)


def test__build_job_explanation():
    iu = InventoryUpdate(id=3, name='I_am_an_Inventory_Update')

    job_explanation = iu._build_job_explanation()

    assert job_explanation == 'Previous Task Canceled: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % (
        'inventory_update',
        'I_am_an_Inventory_Update',
        3,
    )


class TestControlledBySCM:
    def test_clean_source_path_valid(self):
        inv_src = InventorySource(source_path='/not_real/', source='scm')

        inv_src.clean_source_path()

    @pytest.mark.parametrize(
        'source',
        [
            'ec2',
            'manual',
        ],
    )
    def test_clean_source_path_invalid(self, source):
        inv_src = InventorySource(source_path='/not_real/', source=source)

        with pytest.raises(ValidationError):
            inv_src.clean_source_path()

    def test_clean_update_on_launch_update_on_project_update(self):
        inv_src = InventorySource(update_on_project_update=True, update_on_launch=True, source='scm')

        with pytest.raises(ValidationError):
            inv_src.clean_update_on_launch()
