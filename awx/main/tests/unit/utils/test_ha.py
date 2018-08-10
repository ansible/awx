# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

# python
import pytest
import mock

# AWX
from awx.main.utils.ha import (
    AWXCeleryRouter,
)


class TestAddRemoveCeleryWorkerQueues():
    @pytest.fixture
    def instance_generator(self, mocker):
        def fn(hostname='east-1'):
            groups=['east', 'west', 'north', 'south']
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

