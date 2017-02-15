# awx.main.utils.reload
from awx.main.utils import reload


def test_produce_supervisor_command(mocker):
    with mocker.patch.object(reload.subprocess, 'Popen'):
        reload._supervisor_service_restart(['beat', 'callback', 'fact'])
        reload.subprocess.Popen.assert_called_once_with(
            ['supervisorctl', 'restart', 'tower-processes:receiver', 'tower-processes:factcacher'])


def test_routing_of_service_restarts_works(mocker):
    '''
    This tests that the parent restart method will call the appropriate
    service restart methods, depending on which services are given in args
    '''
    with mocker.patch.object(reload, '_uwsgi_reload'):
        with mocker.patch.object(reload, '_reset_celery_thread_pool'):
            with mocker.patch.object(reload, '_supervisor_service_restart'):
                reload.restart_local_services(['uwsgi', 'celery', 'flower', 'daphne'])
                reload._uwsgi_reload.assert_called_once_with()
                reload._reset_celery_thread_pool.assert_called_once_with()
                reload._supervisor_service_restart.assert_called_once_with(['flower', 'daphne'])


def test_routing_of_service_restarts_diables(mocker):
    '''
    Test that methods are not called if not in the args
    '''
    with mocker.patch.object(reload, '_uwsgi_reload'):
        with mocker.patch.object(reload, '_reset_celery_thread_pool'):
            with mocker.patch.object(reload, '_supervisor_service_restart'):
                reload.restart_local_services(['flower'])
                reload._uwsgi_reload.assert_not_called()
                reload._reset_celery_thread_pool.assert_not_called()
                reload._supervisor_service_restart.assert_called_once_with(['flower'])

