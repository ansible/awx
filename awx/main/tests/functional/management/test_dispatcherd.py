import pytest

from awx.main.dispatch.config import get_dispatcherd_config
from awx.main.management.commands.dispatcherd import _hash_config


@pytest.mark.django_db
def test_dispatcherd_config_hash_is_stable(settings, monkeypatch):
    monkeypatch.setenv('AWX_COMPONENT', 'dispatcher')
    settings.CLUSTER_HOST_ID = 'test-node'
    settings.JOB_EVENT_WORKERS = 1
    settings.DISPATCHER_SCHEDULE = {}

    config_one = get_dispatcherd_config(for_service=True)
    config_two = get_dispatcherd_config(for_service=True)

    assert _hash_config(config_one) == _hash_config(config_two)
