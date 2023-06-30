from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Instance
from django.test.utils import override_settings


@pytest.mark.django_db
def test_peers_adding_and_removing(run_module, admin_user):
    with override_settings(IS_K8S=True):
        result = run_module(
            'instance',
            {'hostname': 'hopnode1', 'node_type': 'hop', 'peers_from_control_nodes': True, 'node_state': 'installed', 'listener_port': 27199},
            admin_user,
        )
        assert result['changed']

        hop_node_1 = Instance.objects.get(pk=result.get('id'))

        assert hop_node_1.peers_from_control_nodes == True
        assert hop_node_1.node_type == 'hop'

        result = run_module(
            'instance',
            {'hostname': 'hopnode2', 'node_type': 'hop', 'peers_from_control_nodes': True, 'node_state': 'installed', 'listener_port': 27199},
            admin_user,
        )
        assert result['changed']

        hop_node_2 = Instance.objects.get(pk=result.get('id'))

        result = run_module(
            'instance',
            {'hostname': 'executionnode', 'node_type': 'execution', 'node_state': 'installed', 'listener_port': 27199, 'peers': ['hopnode1', 'hopnode2']},
            admin_user,
        )
        assert result['changed']

        execution_node = Instance.objects.get(pk=result.get('id'))

        assert set(execution_node.peers.all()) == {hop_node_1, hop_node_2}

        result = run_module(
            'instance',
            {'hostname': 'executionnode', 'node_type': 'execution', 'node_state': 'installed', 'listener_port': 27199, 'peers': []},
            admin_user,
        )

        assert result['changed']
        assert set(execution_node.peers.all()) == set()
