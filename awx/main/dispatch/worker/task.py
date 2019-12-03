import inspect
import logging
import importlib
import sys
import traceback

from kubernetes.config import kube_config

from awx.main.tasks import dispatch_startup, inform_cluster_of_shutdown

from .base import BaseWorker

logger = logging.getLogger('awx.main.dispatch')


class TaskWorker(BaseWorker):
    '''
    A worker implementation that deserializes task messages and runs native
    Python code.

    The code that *builds* these types of messages is found in
    `awx.main.dispatch.publish`.
    '''

    @classmethod
    def resolve_callable(cls, task):
        '''
        Transform a dotted notation task into an imported, callable function, e.g.,

        awx.main.tasks.delete_inventory
        awx.main.tasks.RunProjectUpdate
        '''
        if not task.startswith('awx.'):
            raise ValueError('{} is not a valid awx task'.format(task))
        module, target = task.rsplit('.', 1)
        module = importlib.import_module(module)
        _call = None
        if hasattr(module, target):
            _call = getattr(module, target, None)
        if not (
            hasattr(_call, 'apply_async') and hasattr(_call, 'delay')
        ):
            raise ValueError('{} is not decorated with @task()'.format(task))

        return _call

    def run_callable(self, body):
        '''
        Given some AMQP message, import the correct Python code and run it.
        '''
        task = body['task']
        uuid = body.get('uuid', '<unknown>')
        args = body.get('args', [])
        kwargs = body.get('kwargs', {})
        _call = TaskWorker.resolve_callable(task)
        if inspect.isclass(_call):
            # the callable is a class, e.g., RunJob; instantiate and
            # return its `run()` method
            _call = _call().run
        # don't print kwargs, they often contain launch-time secrets
        logger.debug('task {} starting {}(*{})'.format(uuid, task, args))
        return _call(*args, **kwargs)

    def perform_work(self, body):
        '''
        Import and run code for a task e.g.,

        body = {
            'args': [8],
            'callbacks': [{
                'args': [],
                'kwargs': {}
                'task': u'awx.main.tasks.handle_work_success'
            }],
            'errbacks': [{
                'args': [],
                'kwargs': {},
                'task': 'awx.main.tasks.handle_work_error'
            }],
            'kwargs': {},
            'task': u'awx.main.tasks.RunProjectUpdate'
        }
        '''
        result = None
        try:
            result = self.run_callable(body)
        except Exception as exc:
            result = exc

            try:
                if getattr(exc, 'is_awx_task_error', False):
                    # Error caused by user / tracked in job output
                    logger.warning("{}".format(exc))
                else:
                    task = body['task']
                    args = body.get('args', [])
                    kwargs = body.get('kwargs', {})
                    logger.exception('Worker failed to run task {}(*{}, **{}'.format(
                        task, args, kwargs
                    ))
            except Exception:
                # It's fairly critical that this code _not_ raise exceptions on logging
                # If you configure external logging in a way that _it_ fails, there's
                # not a lot we can do here; sys.stderr.write is a final hail mary
                _, _, tb = sys.exc_info()
                traceback.print_tb(tb)

            for callback in body.get('errbacks', []) or []:
                callback['uuid'] = body['uuid']
                self.perform_work(callback)
        finally:
            # It's frustrating that we have to do this, but the python k8s
            # client leaves behind cacert files in /tmp, so we must clean up
            # the tmpdir per-dispatcher process every time a new task comes in
            try:
                kube_config._cleanup_temp_files()
            except Exception:
                logger.exception('failed to cleanup k8s client tmp files')

        for callback in body.get('callbacks', []) or []:
            callback['uuid'] = body['uuid']
            self.perform_work(callback)
        return result

    def on_start(self):
        dispatch_startup()

    def on_stop(self):
        inform_cluster_of_shutdown()
