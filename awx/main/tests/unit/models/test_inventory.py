import pytest

from django.core.exceptions import ValidationError

from awx.main.models import (
    InventorySource,
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
