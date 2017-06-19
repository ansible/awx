# awx.main.utils.reload
from awx.main.utils import reload


def test_produce_supervisor_command(mocker):
    communicate_mock = mocker.MagicMock(return_value=('Everything is fine', ''))
    mock_process = mocker.MagicMock()
    mock_process.communicate = communicate_mock
    Popen_mock = mocker.MagicMock(return_value=mock_process)
    with mocker.patch.object(reload.subprocess, 'Popen', Popen_mock):
        reload._supervisor_service_command(['beat', 'callback', 'fact'], "restart")
        reload.subprocess.Popen.assert_called_once_with(
            ['supervisorctl', 'restart', 'tower-processes:receiver',],
            stderr=-1, stdin=-1, stdout=-1)


def test_routing_of_service_restarts_works(mocker):
    '''
    This tests that the parent restart method will call the appropriate
    service restart methods, depending on which services are given in args
    '''
    with mocker.patch.object(reload, '_uwsgi_fifo_command'),\
            mocker.patch.object(reload, '_reset_celery_thread_pool'),\
            mocker.patch.object(reload, '_supervisor_service_command'):
        reload.restart_local_services(['uwsgi', 'celery', 'flower', 'daphne'])
        reload._uwsgi_fifo_command.assert_called_once_with(uwsgi_command="c")
        reload._reset_celery_thread_pool.assert_called_once_with()
        reload._supervisor_service_command.assert_called_once_with(['flower', 'daphne'], command="restart")



def test_routing_of_service_restarts_diables(mocker):
    '''
    Test that methods are not called if not in the args
    '''
    with mocker.patch.object(reload, '_uwsgi_fifo_command'),\
            mocker.patch.object(reload, '_reset_celery_thread_pool'),\
            mocker.patch.object(reload, '_supervisor_service_command'):
        reload.restart_local_services(['flower'])
        reload._uwsgi_fifo_command.assert_not_called()
        reload._reset_celery_thread_pool.assert_not_called()
        reload._supervisor_service_command.assert_called_once_with(['flower'], command="restart")

