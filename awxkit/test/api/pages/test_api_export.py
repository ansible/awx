from types import SimpleNamespace
from unittest import mock

import pytest

from awxkit.api.pages.api import ApiV2


class _ReachedCreate(Exception):
    """Raised by a fake related endpoint to prove export did not skip it."""


def _make_related_endpoint():
    endpoint = mock.Mock()
    endpoint._create.side_effect = _ReachedCreate()
    return endpoint


def _make_inventory_page(kind):
    natural_key = {'type': 'inventory', 'name': 'inv'}
    return SimpleNamespace(
        __item_class__=SimpleNamespace(__name__='Inventory'),
        json={'kind': kind},
        related={'hosts': _make_related_endpoint(), 'groups': _make_related_endpoint()},
        get_natural_key=lambda cache: natural_key,
    )


def _export(page):
    # ``self`` only needs the attributes _export touches on the paths under test.
    api = SimpleNamespace(_cache=mock.Mock(), _has_error=False)
    return ApiV2._export(api, page, post_fields={})


@pytest.mark.parametrize('kind', ['smart', 'constructed'])
def test_export_skips_hosts_and_groups_for_computed_inventories(kind):
    # Smart/constructed inventories generate hosts and groups dynamically; they
    # cannot be recreated on import, so they must not be exported (AAP-30037).
    result = _export(_make_inventory_page(kind))

    assert 'related' not in result
    assert result['natural_key'] == {'type': 'inventory', 'name': 'inv'}


def test_export_still_processes_hosts_and_groups_for_standard_inventories():
    # A standard inventory owns its hosts/groups, so export must still reach the
    # related endpoints (proven here by the sentinel raised in ``_create``).
    with pytest.raises(_ReachedCreate):
        _export(_make_inventory_page(''))
