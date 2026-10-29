import pytest

from django.core.exceptions import ValidationError

from awx.main.models import (
    InventoryUpdate,
    InventorySource,
)


def test__build_job_explanation():
    iu = InventoryUpdate(id=3, name='I_am_an_Inventory_Update')

    job_explanation = iu._build_job_explanation()

    assert job_explanation == 'Previous Task Canceled: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % (
        'inventory_update',
        'I_am_an_Inventory_Update',
        3,
    )


class TestSourceVarsPreventSearch:
    """source_vars must be wrapped with prevent_search() so that the REST
    filter backend rejects filter lookups on it (e.g.
    ``source_vars__contains``).  Without this guard a zero-privilege user
    can use ORM join filters as a count-oracle to exfiltrate inline
    credentials stored in source_vars.
    """

    def test_source_vars_is_not_searchable(self):
        """The guard REJECTS: source_vars must carry __prevent_search__."""
        field = InventorySource._meta.get_field('source_vars')
        assert getattr(field, '__prevent_search__', False) is True

    def test_source_field_remains_searchable(self):
        """The guard PERMITS: neighbouring fields that were never wrapped
        must stay searchable (no __prevent_search__ attribute)."""
        field = InventorySource._meta.get_field('source')
        assert getattr(field, '__prevent_search__', False) is False


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
