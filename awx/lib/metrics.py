# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from functools import wraps
from django_statsd.clients import statsd

logger = logging.getLogger(__name__)


def task_timer(fn):
    @wraps(fn)
    def __wrapped__(self, *args, **kwargs):
        statsd.incr('tasks.{0}.{1}.count'.format(
            self.name.rsplit('.', 1)[-1],
            fn.__name__))
        with statsd.timer('tasks.{0}.{1}.timer'.format(
                self.name.rsplit('.', 1)[-1],
                fn.__name__)):
            return fn(self, *args, **kwargs)
    return __wrapped__


class BaseTimer(object):
    def __init__(self, name, prefix=None):
        self.name = name.rsplit('.', 1)[-1]
        if prefix:
            self.name = '{0}.{1}'.format(prefix, self.name)

    def __call__(self, fn):
        @wraps(fn)
        def __wrapped__(obj, *args, **kwargs):
            statsd.incr('{0}.{1}.count'.format(
                self.name,
                fn.__name__
            ))
            with statsd.timer('{0}.{1}.timer'.format(
                    self.name,
                    fn.__name__
            )):
                return fn(obj, *args, **kwargs)
        return __wrapped__
