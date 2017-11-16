# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

# python
import pytest
import mock

# AWX
from awx.main.utils.ha import (
    _add_remove_celery_worker_queues,
    update_celery_worker_routes,
)


@pytest.fixture
def conf():
    class Conf():
        CELERY_TASK_ROUTES = dict()
        CELERYBEAT_SCHEDULE = dict()
    return Conf()


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

    @pytest.mark.parametrize("static_queues,_worker_queues,groups,hostname,added_expected,removed_expected", [
        (['east', 'west'], ['east', 'west', 'east-1'], [], 'east-1', [], []),
        ([], ['east', 'west', 'east-1'], ['east', 'west'], 'east-1', [], []),
        ([], ['east', 'west'], ['east', 'west'], 'east-1', ['east-1'], []),
        ([], [], ['east', 'west'], 'east-1', ['east', 'west', 'east-1'], []),
        ([], ['china', 'russia'], ['east', 'west'], 'east-1', ['east', 'west', 'east-1'], ['china', 'russia']),
    ])
    def test__add_remove_celery_worker_queues_noop(self, mock_app,
                                                   instance_generator, 
                                                   worker_queues_generator, 
                                                   static_queues, _worker_queues, 
                                                   groups, hostname,
                                                   added_expected, removed_expected):
        instance = instance_generator(groups=groups, hostname=hostname)
        worker_queues = worker_queues_generator(_worker_queues)
        with mock.patch('awx.main.utils.ha.settings.AWX_CELERY_QUEUES_STATIC', static_queues):
            (added_queues, removed_queues) = _add_remove_celery_worker_queues(mock_app, instance, worker_queues, hostname)
            assert set(added_queues) == set(added_expected)
            assert set(removed_queues) == set(removed_expected)


class TestUpdateCeleryWorkerRoutes():

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
    def test_update_celery_worker_routes(self, mocker, conf, is_controller, expected_routes):
        instance = mocker.MagicMock()
        instance.hostname = 'east-1'
        instance.is_controller = mocker.MagicMock(return_value=is_controller)

        assert update_celery_worker_routes(instance, conf) == expected_routes
        assert conf.CELERY_TASK_ROUTES == expected_routes

    def test_update_celery_worker_routes_deleted(self, mocker, conf):
        instance = mocker.MagicMock()
        instance.hostname = 'east-1'
        instance.is_controller = mocker.MagicMock(return_value=False)
        conf.CELERY_TASK_ROUTES = {'awx.main.tasks.awx_isolated_heartbeat': 'foobar'}

        update_celery_worker_routes(instance, conf)
        assert 'awx.main.tasks.awx_isolated_heartbeat' not in conf.CELERY_TASK_ROUTES

