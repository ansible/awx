import copy
import json
import logging
import os
import tempfile
import shutil
from unittest import mock

import pytest

from awx.main.tasks.system import CleanupImagesAndFiles, execution_node_health_check, inspect_established_receptor_connections, clear_setting_cache
from awx.main.management.commands.run_dispatcher import Command
from awx.main.models import Instance, Job, ReceptorAddress, InstanceLink


@pytest.mark.django_db
class TestLinkState:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.IS_K8S = True

    def test_inspect_established_receptor_connections(self):
        '''
        Change link state from ADDING to ESTABLISHED
        if the receptor status KnownConnectionCosts field
        has an entry for the source and target node.
        '''
        hop1 = Instance.objects.create(hostname='hop1')
        hop2 = Instance.objects.create(hostname='hop2')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', port=5678)
        InstanceLink.objects.create(source=hop1, target=hop2addr, link_state=InstanceLink.States.ADDING)

        # calling with empty KnownConnectionCosts should not change the link state
        inspect_established_receptor_connections({"KnownConnectionCosts": {}})
        assert InstanceLink.objects.get(source=hop1, target=hop2addr).link_state == InstanceLink.States.ADDING

        mesh_state = {"KnownConnectionCosts": {"hop1": {"hop2": 1}}}
        inspect_established_receptor_connections(mesh_state)
        assert InstanceLink.objects.get(source=hop1, target=hop2addr).link_state == InstanceLink.States.ESTABLISHED


@pytest.fixture
def job_folder_factory(request):
    def _rf(job_id='1234'):
        pdd_path = tempfile.mkdtemp(prefix=f'awx_{job_id}_')

        def test_folder_cleanup():
            if os.path.exists(pdd_path):
                shutil.rmtree(pdd_path)

        request.addfinalizer(test_folder_cleanup)

        return pdd_path

    return _rf


@pytest.fixture
def mock_job_folder(job_folder_factory):
    return job_folder_factory()


@pytest.mark.django_db
@pytest.mark.parametrize('node_type', ('control. hybrid'))
def test_no_worker_info_on_AWX_nodes(node_type):
    hostname = 'us-south-3-compute.invalid'
    Instance.objects.create(hostname=hostname, node_type=node_type)
    assert execution_node_health_check(hostname) is None


@pytest.mark.django_db
def test_folder_cleanup_stale_file(mock_job_folder, mock_me):
    CleanupImagesAndFiles.run()
    assert os.path.exists(mock_job_folder)  # grace period should protect folder from deletion

    CleanupImagesAndFiles.run(grace_period=0)
    assert not os.path.exists(mock_job_folder)  # should be deleted


@pytest.mark.django_db
def test_folder_cleanup_running_job(mock_job_folder, me_inst):
    job = Job.objects.create(id=1234, controller_node=me_inst.hostname, status='running')
    CleanupImagesAndFiles.run(grace_period=0)
    assert os.path.exists(mock_job_folder)  # running job should prevent folder from getting deleted

    job.status = 'failed'
    job.save(update_fields=['status'])
    CleanupImagesAndFiles.run(grace_period=0)
    assert not os.path.exists(mock_job_folder)  # job is finished and no grace period, should delete


@pytest.mark.django_db
def test_folder_cleanup_multiple_running_jobs(job_folder_factory, me_inst):
    jobs = []
    dirs = []
    num_jobs = 3

    for i in range(num_jobs):
        job = Job.objects.create(controller_node=me_inst.hostname, status='running')
        dirs.append(job_folder_factory(job.id))
        jobs.append(job)

    CleanupImagesAndFiles.run(grace_period=0)

    assert [os.path.exists(d) for d in dirs] == [True for i in range(num_jobs)]


@pytest.mark.django_db
def test_clear_setting_cache_log_level_branch(settings):
    settings.LOG_AGGREGATOR_LEVEL = 'DEBUG'
    settings.CLUSTER_HOST_ID = 'control-node'
    published_messages = []

    class DummyBroker:
        def publish_message(self, channel, message):
            published_messages.append((channel, message))

        def close(self):
            pass

    dummy_broker = DummyBroker()

    with mock.patch('dispatcherd.control.get_broker', return_value=dummy_broker) as mock_get_broker:
        clear_setting_cache(['LOG_AGGREGATOR_LEVEL'])

    mock_get_broker.assert_called_once()
    assert published_messages, 'control command was not sent through the broker'
    queue, payload = published_messages[-1]
    assert queue == 'control-node'
    body = json.loads(payload)
    assert body['control'] == 'set_log_level'
    assert body['control_data'] == {'level': 'DEBUG'}


@pytest.mark.django_db
def test_configure_dispatcher_logging_updates_level(settings):
    original_logging_settings = copy.deepcopy(settings.LOGGING)
    settings.LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'dynamic_level_filter': {
                '()': 'logging.Filter',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'filters': ['dynamic_level_filter'],
                'stream': 'ext://sys.stdout',
            }
        },
        'loggers': {
            'dispatcherd': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            }
        },
    }
    settings.LOG_AGGREGATOR_LEVEL = 'WARNING'

    Command().configure_dispatcher_logging()

    assert logging.getLogger('dispatcherd').level == logging.WARNING
    settings.LOGGING = original_logging_settings
