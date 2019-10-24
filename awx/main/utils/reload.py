# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import subprocess
import logging

# Django
from django.conf import settings

logger = logging.getLogger('awx.main.utils.reload')


def supervisor_service_command(command, service='*', communicate=True):
    '''
    example use pattern of supervisorctl:
    # supervisorctl restart tower-processes:receiver tower-processes:factcacher
    '''
    args = ['supervisorctl']
    args.extend([command, ':'.join(['tower-processes', service])])
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


def stop_local_services(communicate=True):
    logger.warn('Stopping services on this node in response to user action')
    supervisor_service_command(command='stop', communicate=communicate)
