import inspect
import logging
import sys
import json
from uuid import uuid4
import psycopg2

from django.conf import settings
from kombu import Exchange, Producer
from django.db import connection
from pgpubsub import PubSub

from awx.main.dispatch.kombu import Connection

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

    # Tasks can also define a specific target queue or exchange type:

    @task(queue='slow-tasks')
    def snooze():
        time.sleep(10)

    @task(queue='tower_broadcast', exchange_type='fanout')
    def announce():
        print("Run this everywhere!")
    """

    def __init__(self, queue=None, exchange_type=None):
        self.queue = queue
        self.exchange_type = exchange_type

    def __call__(self, fn=None):
        queue = self.queue
        exchange_type = self.exchange_type

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
                    getattr(cls.queue, 'im_func', cls.queue) or
                    settings.CELERY_DEFAULT_QUEUE
                )
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
                    conf = settings.DATABASES['default']
                    conn = psycopg2.connect(dbname=conf['NAME'],
                                            host=conf['HOST'],
                                            user=conf['USER'],
                                            password=conf['PASSWORD'])
                    conn.set_session(autocommit=True)
                    logger.warn(f"Send message to queue {queue}")
                    pubsub = PubSub(conn)
                    pubsub.notify(queue, json.dumps(obj))
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
