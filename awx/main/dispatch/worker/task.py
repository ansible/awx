import logging
import importlib
import time

from django_guid import set_guid

logger = logging.getLogger('awx.main.dispatch')


def resolve_callable(task):
    """
    Transform a dotted notation task into an imported, callable function, e.g.,
    awx.main.tasks.system.delete_inventory
    awx.main.tasks.jobs.RunProjectUpdate
    """
    if not task.startswith('awx.'):
        raise ValueError('{} is not a valid awx task'.format(task))
    module, target = task.rsplit('.', 1)
    module = importlib.import_module(module)
    _call = None
    if hasattr(module, target):
        _call = getattr(module, target, None)
    if not (hasattr(_call, 'apply_async') and hasattr(_call, 'delay')):
        raise ValueError('{} is not decorated with @task()'.format(task))
    return _call


def run_callable(body):
    """
    Given some AMQP message, import the correct Python code and run it.
    """
    task = body['task']
    uuid = body.get('uuid', '<unknown>')
    args = body.get('args', [])
    kwargs = body.get('kwargs', {})
    if 'guid' in body:
        set_guid(body.pop('guid'))
    _call = resolve_callable(task)
    log_extra = ''
    logger_method = logger.debug
    if 'time_pub' in body:
        time_publish = time.time() - body['time_pub']
        if time_publish > 5.0:
            # If task too a very long time to process, add this information to the log
            log_extra = f' took {time_publish:.4f} to send message'
            logger_method = logger.info
    # don't print kwargs, they often contain launch-time secrets
    logger_method(f'task {uuid} starting {task}(*{args}){log_extra}')
    return _call(*args, **kwargs)
