from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Instance
from django.test.utils import override_settings


@pytest.mark.filterwarnings(
    # FIXME: Figure out where it is emited and what causes it.
    # FIXME: The suppression should be made more specific or the cause fixed.
    # Ref: https://github.com/ansible/awx/pull/15620
    "ignore::RuntimeWarning",
)
@pytest.mark.django_db
def test_peers_adding_and_removing(run_module, admin_user):
    with override_settings(IS_K8S=True):
        result = run_module(
            'instance',
            {'hostname': 'hopnode', 'node_type': 'hop', 'node_state': 'installed', 'listener_port': 6789},
            admin_user,
        )
        assert result['changed']

        hop_node = Instance.objects.get(pk=result.get('id'))

        assert hop_node.node_type == 'hop'

        address = hop_node.receptor_addresses.get(pk=result.get('id'))
        assert address.port == 6789

        result = run_module(
            'instance',
            {'hostname': 'executionnode', 'node_type': 'execution', 'node_state': 'installed', 'peers': ['hopnode']},
            admin_user,
        )
        assert result['changed']

        execution_node = Instance.objects.get(pk=result.get('id'))

        assert set(execution_node.peers.all()) == {address}

        result = run_module(
            'instance',
            {'hostname': 'executionnode', 'node_type': 'execution', 'node_state': 'installed', 'peers': []},
            admin_user,
        )

        assert result['changed']
        assert set(execution_node.peers.all()) == set()
