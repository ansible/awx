# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

# python
import pytest
import mock
from contextlib import nested

# AWX
from awx.main.utils.ha import (
    _add_remove_celery_worker_queues,
    AWXCeleryRouter,
)


class TestAddRemoveCeleryWorkerQueues():
    @pytest.fixture
    def instance_generator(self, mocker):
        def fn(groups=['east', 'west', 'north', 'south'], hostname='east-1'):
            instance = mocker.MagicMock()
            instance.hostname = hostname
            instance.rampart_groups = mocker.MagicMock()
            instance.rampart_groups.values_list = mocker.MagicMock(return_value=groups)

            return instance
        return fn

    @pytest.fixture
    def worker_queues_generator(self, mocker):
        def fn(queues=['east', 'west']):
            return [dict(name=n, alias='') for n in queues]
        return fn

    @pytest.fixture
    def mock_app(self, mocker):
        app = mocker.MagicMock()
        app.control = mocker.MagicMock()
        app.control.cancel_consumer = mocker.MagicMock()
        return app

    @pytest.mark.parametrize("broadcast_queues,static_queues,_worker_queues,groups,hostname,added_expected,removed_expected", [
        (['tower_broadcast_all'], ['east', 'west'], ['east', 'west', 'east-1'], [], 'east-1', ['tower_broadcast_all_east-1'], []),
        ([], [], ['east', 'west', 'east-1'], ['east', 'west'], 'east-1', [], []),
        ([], [], ['east', 'west'], ['east', 'west'], 'east-1', ['east-1'], []),
        ([], [], [], ['east', 'west'], 'east-1', ['east', 'west', 'east-1'], []),
        ([], [], ['china', 'russia'], ['east', 'west'], 'east-1', ['east', 'west', 'east-1'], ['china', 'russia']),
    ])
    def test__add_remove_celery_worker_queues_noop(self, mock_app,
                                                   instance_generator,
                                                   worker_queues_generator,
                                                   broadcast_queues,
                                                   static_queues, _worker_queues,
                                                   groups, hostname,
                                                   added_expected, removed_expected):
        instance = instance_generator(groups=groups, hostname=hostname)
        worker_queues = worker_queues_generator(_worker_queues)
        with nested(
                mock.patch('awx.main.utils.ha.settings.AWX_CELERY_QUEUES_STATIC', static_queues),
                mock.patch('awx.main.utils.ha.settings.AWX_CELERY_BCAST_QUEUES_STATIC', broadcast_queues),
                mock.patch('awx.main.utils.ha.settings.CLUSTER_HOST_ID', hostname)):
            (added_queues, removed_queues) = _add_remove_celery_worker_queues(mock_app, [instance], worker_queues, hostname)
            assert set(added_queues) == set(added_expected)
            assert set(removed_queues) == set(removed_expected)


class TestUpdateCeleryWorkerRouter():

    @pytest.mark.parametrize("is_controller,expected_routes", [
        (False, {
            'awx.main.tasks.cluster_node_heartbeat': {'queue': 'east-1', 'routing_key': 'east-1'},
            'awx.main.tasks.purge_old_stdout_files': {'queue': 'east-1', 'routing_key': 'east-1'}
        }),
        (True, {
            'awx.main.tasks.cluster_node_heartbeat': {'queue': 'east-1', 'routing_key': 'east-1'},
            'awx.main.tasks.purge_old_stdout_files': {'queue': 'east-1', 'routing_key': 'east-1'},
            'awx.main.tasks.awx_isolated_heartbeat': {'queue': 'east-1', 'routing_key': 'east-1'},
        }),
    ])
    def test_update_celery_worker_routes(self, mocker, is_controller, expected_routes):
        def get_or_register():
            instance = mock.MagicMock()
            instance.hostname = 'east-1'
            instance.is_controller = mock.MagicMock(return_value=is_controller)
            return (False, instance)

        with mock.patch('awx.main.models.Instance.objects.get_or_register', get_or_register):
            router = AWXCeleryRouter()

            for k,v in expected_routes.iteritems():
                assert router.route_for_task(k) == v

