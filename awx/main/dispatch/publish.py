import inspect
import logging
import sys
import json
from uuid import uuid4

from django.conf import settings

from . import pg_bus_conn

logger = logging.getLogger('awx.main.dispatch')


def serialize_task(f):
    return '.'.join([f.__module__, f.__name__])


class task:
    """
    Used to decorate a function or class so that it can be run asynchronously
    via the task dispatcher.  Tasks can be simple functions:

    @task()
    def add(a, b):
        return a + b

    ...or classes that define a `run` method:

    @task()
    class Adder:
        def run(self, a, b):
            return a + b

    # Tasks can be run synchronously...
    assert add(1, 1) == 2
    assert Adder().run(1, 1) == 2

    # ...or published to a queue:
    add.apply_async([1, 1])
    Adder.apply_async([1, 1])

    # Tasks can also define a specific target queue or use the special fan-out queue tower_broadcast:

    @task(queue='slow-tasks')
    def snooze():
        time.sleep(10)

    @task(queue='tower_broadcast')
    def announce():
        print("Run this everywhere!")
    """

    def __init__(self, queue=None):
        self.queue = queue

    def __call__(self, fn=None):
        queue = self.queue

        class PublisherMixin(object):

            queue = None

            @classmethod
            def delay(cls, *args, **kwargs):
                return cls.apply_async(args, kwargs)

            @classmethod
            def apply_async(cls, args=None, kwargs=None, queue=None, uuid=None, **kw):
                task_id = uuid or str(uuid4())
                args = args or []
                kwargs = kwargs or {}
                queue = (
                    queue or
                    getattr(cls.queue, 'im_func', cls.queue)
                )
                if not queue:
                    msg = f'{cls.name}: Queue value required and may not be None'
                    logger.error(msg)
                    raise ValueError(msg)
                obj = {
                    'uuid': task_id,
                    'args': args,
                    'kwargs': kwargs,
                    'task': cls.name
                }
                obj.update(**kw)
                if callable(queue):
                    queue = queue()
                if not settings.IS_TESTING(sys.argv):
                    with pg_bus_conn() as conn:
                        conn.notify(queue, json.dumps(obj))
                return (obj, queue)

        # If the object we're wrapping *is* a class (e.g., RunJob), return
        # a *new* class that inherits from the wrapped class *and* BaseTask
        # In this way, the new class returned by our decorator is the class
        # being decorated *plus* PublisherMixin so cls.apply_async() and
        # cls.delay() work
        bases = []
        ns = {'name': serialize_task(fn), 'queue': queue}
        if inspect.isclass(fn):
            bases = list(fn.__bases__)
            ns.update(fn.__dict__)
        cls = type(
            fn.__name__,
            tuple(bases + [PublisherMixin]),
            ns
        )
        if inspect.isclass(fn):
            return cls

        # if the object being decorated is *not* a class (it's a Python
        # function), make fn.apply_async and fn.delay proxy through to the
        # PublisherMixin we dynamically created above
        setattr(fn, 'name', cls.name)
        setattr(fn, 'apply_async', cls.apply_async)
        setattr(fn, 'delay', cls.delay)
        return fn
