# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import subprocess
import logging

# Django
from django.conf import settings

# Celery
from celery import current_app

logger = logging.getLogger('awx.main.utils.reload')


def _uwsgi_fifo_command(uwsgi_command):
    # http://uwsgi-docs.readthedocs.io/en/latest/MasterFIFO.html#available-commands
    logger.warn('Initiating uWSGI chain reload of server')
    TRIGGER_COMMAND = uwsgi_command
    with open(settings.UWSGI_FIFO_LOCATION, 'w') as awxfifo:
        awxfifo.write(TRIGGER_COMMAND)


def _reset_celery_thread_pool():
    # Send signal to restart thread pool
    app = current_app._get_current_object()
    app.control.broadcast('pool_restart', arguments={'reload': True},
                          destination=['celery@{}'.format(settings.CLUSTER_HOST_ID)], reply=False)


def _supervisor_service_command(service_internal_names, command, communicate=True):
    '''
    Service internal name options:
     - beat - celery - callback - channels - uwsgi - daphne
     - fact - nginx
    example use pattern of supervisorctl:
    # supervisorctl restart tower-processes:receiver tower-processes:factcacher
    '''
    group_name = 'tower-processes'
    if settings.DEBUG:
        group_name = 'awx-processes'
    args = ['supervisorctl']
    if settings.DEBUG:
        args.extend(['-c', '/supervisor.conf'])
    programs = []
    name_translation_dict = settings.SERVICE_NAME_DICT
    for n in service_internal_names:
        if n in name_translation_dict:
            programs.append('{}:{}'.format(group_name, name_translation_dict[n]))
    args.extend([command])
    args.extend(programs)
    logger.debug('Issuing command to {} services, args={}'.format(command, args))
    supervisor_process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if communicate:
        restart_stdout, restart_err = supervisor_process.communicate()
        restart_code = supervisor_process.returncode
        if restart_code or restart_err:
            logger.error('supervisorctl {} errored with exit code `{}`, stdout:\n{}stderr:\n{}'.format(
                command, restart_code, restart_stdout.strip(), restart_err.strip()))
        else:
            logger.info('supervisorctl {} finished, stdout:\n{}'.format(
                command, restart_stdout.strip()))
    else:
        logger.info('Submitted supervisorctl {} command, not waiting for result'.format(command))


def restart_local_services(service_internal_names):
    logger.warn('Restarting services {} on this node in response to user action'.format(service_internal_names))
    if 'uwsgi' in service_internal_names:
        _uwsgi_fifo_command(uwsgi_command='c')
        service_internal_names.remove('uwsgi')
    restart_celery = False
    if 'celery' in service_internal_names:
        restart_celery = True
        service_internal_names.remove('celery')
    _supervisor_service_command(service_internal_names, command='restart')
    if restart_celery:
        # Celery restarted last because this probably includes current process
        _reset_celery_thread_pool()


def stop_local_services(service_internal_names, communicate=True):
    logger.warn('Stopping services {} on this node in response to user action'.format(service_internal_names))
    _supervisor_service_command(service_internal_names, command='stop', communicate=communicate)
