import time
import logging

from dispatcherd.publish import task

from django.db import connection

from awx.main.dispatch import get_task_queuename
from awx.main.dispatch.publish import task as old_task

from ansible_base.lib.utils.db import advisory_lock


logger = logging.getLogger(__name__)


@old_task(queue=get_task_queuename)
def sleep_task(seconds=10, log=False):
    if log:
        logger.info('starting sleep_task')
    time.sleep(seconds)
    if log:
        logger.info('finished sleep_task')


@task()
def sleep_break_connection(seconds=0.2):
    """
    Interact with the database in an intentionally breaking way.
    After this finishes, queries made by this connection are expected to error
    with "the connection is closed"
    This is obviously a problem for any task that comes afterwards.
    So this is used to break things so that the fixes may be demonstrated.
    """
    with connection.cursor() as cursor:
        cursor.execute(f"SET idle_session_timeout = '{seconds / 2}s';")

    logger.info(f'sleeping for {seconds}s > {seconds / 2}s session timeout')
    time.sleep(seconds)

    for i in range(1, 3):
        logger.info(f'\nRunning query number {i}')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                logger.info('  query worked, not expected')
        except Exception as exc:
            logger.info(f'  query errored as expected\ntype: {type(exc)}\nstr: {str(exc)}')

    logger.info(f'Connection present: {bool(connection.connection)}, reports closed: {getattr(connection.connection, "closed", "not_found")}')


@task()
def advisory_lock_exception():
    time.sleep(0.2)  # so it can fill up all the workers... hacky for now
    with advisory_lock('advisory_lock_exception', lock_session_timeout_milliseconds=20):
        raise RuntimeError('this is an intentional error')
