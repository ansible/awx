from contextlib import contextmanager

import pytest
import yaml

from awx.main.models import (
    UnifiedJob,
    Notification,
)

from awx.main import tasks
from awx.main.task_engine import TaskEnhancer


@contextmanager
def apply_patches(_patches):
    [p.start() for p in _patches]
    yield
    [p.stop() for p in _patches]


def test_send_notifications_not_list():
    with pytest.raises(TypeError):
        tasks.send_notifications(None)


def test_send_notifications_job_id(mocker):
    with mocker.patch('awx.main.models.UnifiedJob.objects.get'):
        tasks.send_notifications([], job_id=1)
        assert UnifiedJob.objects.get.called
        assert UnifiedJob.objects.get.called_with(id=1)


def test_send_notifications_list(mocker):
    patches = list()

    mock_job = mocker.MagicMock(spec=UnifiedJob)
    patches.append(mocker.patch('awx.main.models.UnifiedJob.objects.get', return_value=mock_job))

    mock_notifications = [mocker.MagicMock(spec=Notification, subject="test", body={'hello': 'world'})]
    patches.append(mocker.patch('awx.main.models.Notification.objects.filter', return_value=mock_notifications))

    with apply_patches(patches):
        tasks.send_notifications([1,2], job_id=1)
        assert Notification.objects.filter.call_count == 1
        assert mock_notifications[0].status == "successful"
        assert mock_notifications[0].save.called

        assert mock_job.notifications.add.called
        assert mock_job.notifications.add.called_with(*mock_notifications)


@pytest.mark.parametrize("current_instances,call_count", [(91, 2), (89,1)])
def test_run_admin_checks_usage(mocker, current_instances, call_count):
    patches = list()
    patches.append(mocker.patch('awx.main.tasks.User'))

    mock_te = mocker.Mock(spec=TaskEnhancer)
    mock_te.validate_enhancements.return_value = {'instance_count': 100, 'current_instances': current_instances, 'date_warning': True}
    patches.append(mocker.patch('awx.main.tasks.TaskEnhancer', return_value=mock_te))

    mock_sm = mocker.Mock()
    patches.append(mocker.patch('awx.main.tasks.send_mail', wraps=mock_sm))

    with apply_patches(patches):
        tasks.run_administrative_checks()
        assert mock_sm.called
        if call_count == 2:
            assert '90%' in mock_sm.call_args_list[0][0][0]
        else:
            assert 'expire' in mock_sm.call_args_list[0][0][0]


@pytest.mark.parametrize("key,value", [
    ('REST_API_TOKEN', 'SECRET'),
    ('SECRET_KEY', 'SECRET'),
    ('RABBITMQ_PASS', 'SECRET'),
    ('VMWARE_PASSWORD', 'SECRET'),
    ('API_SECRET', 'SECRET'),
    ('CALLBACK_CONNECTION', 'amqp://tower:password@localhost:5672/tower'),
])
def test_safe_env_filtering(key, value):
    task = tasks.RunJob()
    assert task.build_safe_env({key: value})[key] == tasks.HIDDEN_PASSWORD


def test_safe_env_returns_new_copy():
    task = tasks.RunJob()
    env = {'foo': 'bar'}
    assert task.build_safe_env(env) is not env


def test_openstack_client_config_generation(mocker):
    update = tasks.RunInventoryUpdate()
    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'credential.host': 'https://keystone.openstack.example.org',
        'credential.username': 'demo',
        'credential.password': 'secrete',
        'credential.project': 'demo-project',
        'credential.domain': None,
        'source_vars_dict': {}
    })
    cloud_config = update.build_private_data(inventory_update)
    cloud_credential = yaml.load(cloud_config['cloud_credential'])
    assert cloud_credential['clouds'] == {
        'devstack': {
            'auth': {
                'auth_url': 'https://keystone.openstack.example.org',
                'password': 'secrete',
                'project_name': 'demo-project',
                'username': 'demo'
            },
            'private': True
        }
    }


@pytest.mark.parametrize("source,expected", [
    (False, False), (True, True)
])
def test_openstack_client_config_generation_with_private_source_vars(mocker, source, expected):
    update = tasks.RunInventoryUpdate()
    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'credential.host': 'https://keystone.openstack.example.org',
        'credential.username': 'demo',
        'credential.password': 'secrete',
        'credential.project': 'demo-project',
        'credential.domain': None,
        'source_vars_dict': {'private': source}
    })
    cloud_config = update.build_private_data(inventory_update)
    cloud_credential = yaml.load(cloud_config['cloud_credential'])
    assert cloud_credential['clouds'] == {
        'devstack': {
            'auth': {
                'auth_url': 'https://keystone.openstack.example.org',
                'password': 'secrete',
                'project_name': 'demo-project',
                'username': 'demo'
            },
            'private': expected
        }
    }
