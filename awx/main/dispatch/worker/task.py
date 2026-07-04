import logging
import importlib
import time

from django_guid import set_guid
from opentelemetry.trace import get_tracer, Status, StatusCode

logger = logging.getLogger('awx.main.dispatch')
tracer = get_tracer(__name__)


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

    # Extract task name components for span naming
    # task = "awx.main.tasks.system.apply_cluster_membership_policies"
    task_module, task_function = task.rsplit('.', 1)

    # Create span with task function name (like HTTP route)
    with tracer.start_as_current_span(task_function) as span:
        # Set rich span attributes
        span.set_attribute("task.name", task)
        span.set_attribute("task.uuid", uuid)
        span.set_attribute("task.module", task_module)
        span.set_attribute("task.function", task_function)
        span.set_attribute("task.args_count", len(args))
        span.set_attribute("task.kwargs_count", len(kwargs))

        # Add correlation ID if available
        if 'guid' in body:
            guid = body['guid']
            span.set_attribute("correlation_id", guid)
            set_guid(body.pop('guid'))

        # Calculate message delay if publish time available
        log_extra = ''
        logger_method = logger.debug
        if 'time_pub' in body:
            time_publish = time.time() - body['time_pub']
            delay_ms = time_publish * 1000
            span.set_attribute("task.message_delay_ms", delay_ms)

            if time_publish > 5.0:
                # If task took a very long time to process, add this information to the log
                log_extra = f' took {time_publish:.4f} to send message'
                logger_method = logger.info

        try:
            # Resolve and execute task
            _call = resolve_callable(task)
            # don't print kwargs, they often contain launch-time secrets
            logger_method(f'task {uuid} starting {task}(*{args}){log_extra}')

            result = _call(*args, **kwargs)

            # Mark span as successful
            span.set_status(Status(StatusCode.OK))
            return result

        except Exception as e:
            # Record exception in span
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("task.error_type", type(e).__name__)
            span.set_attribute("task.error_message", str(e))
            span.record_exception(e)
            raise
