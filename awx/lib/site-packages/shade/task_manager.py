#!/usr/bin/env python

# Copyright (C) 2011-2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import sys
import logging
import time

import six


@six.add_metaclass(abc.ABCMeta)
class Task(object):
    def __init__(self, **kw):
        self._exception = None
        self._traceback = None
        self._result = None
        self.args = kw

    @abc.abstractmethod
    def main(self, client):
        """ Override this method with the actual workload to be performed """

    def done(self, result):
        self._result = result

    def exception(self, e, tb):
        self._exception = e
        self._traceback = tb

    def wait(self):
        if self._exception:
            six.reraise(self._exception, None, self._traceback)
        return self._result

    def run(self, client):
        try:
            self.done(self.main(client))
        except Exception as e:
            self.exception(e, sys.exc_info()[2])


class TaskManager(object):
    log = logging.getLogger("shade.TaskManager")

    def __init__(self, client, name):
        self.name = name
        self._client = client

    def stop(self):
        """ This is a direct action passthrough TaskManager """
        pass

    def run(self):
        """ This is a direct action passthrough TaskManager """
        pass

    def submitTask(self, task):
        self.log.debug(
            "Manager %s running task %s" % (self.name, type(task).__name__))
        start = time.time()
        task.run(self._client)
        end = time.time()
        self.log.debug(
            "Manager %s ran task %s in %ss" % (self.name, task, (end - start)))
        return task.wait()
