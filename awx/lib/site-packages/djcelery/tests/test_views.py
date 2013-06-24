from __future__ import absolute_import

import sys

from functools import partial

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.test.testcases import TestCase as DjangoTestCase
from django.template import TemplateDoesNotExist

from anyjson import deserialize

from celery import current_app
from celery import states
from celery.datastructures import ExceptionInfo
from celery.task import task
from celery.utils import gen_unique_id, get_full_cls_name

from djcelery.views import task_webhook
from djcelery.tests.req import MockRequest


def reversestar(name, **kwargs):
    return reverse(name, kwargs=kwargs)


class MyError(Exception):
    # On Py2.4 repr(exc) includes the object id, so comparing
    # texts is pointless when the id the "same" KeyError does not match.

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.args)


class MyRetryTaskError(Exception):

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.args)


task_is_successful = partial(reversestar, 'celery-is_task_successful')
task_status = partial(reversestar, 'celery-task_status')
task_apply = partial(reverse, 'celery-apply')
registered_tasks = partial(reverse, 'celery-tasks')
scratch = {}


@task()
def mytask(x, y):
    ret = scratch['result'] = int(x) * int(y)
    return ret


def create_exception(name, base=Exception):
    return type(name, (base, ), {})


def catch_exception(exception):
    try:
        raise exception
    except exception.__class__, exc:
        exc = current_app.backend.prepare_exception(exc)
        return exc, ExceptionInfo(sys.exc_info()).traceback


class ViewTestCase(DjangoTestCase):

    def assertJSONEqual(self, json, py):
        json = isinstance(json, HttpResponse) and json.content or json
        try:
            self.assertEqual(deserialize(json), py)
        except TypeError, exc:
            raise TypeError('%s: %s' % (exc, json))

    def assertIn(self, expected, source, *args):
        try:
            DjangoTestCase.assertIn(self, expected, source, *args)
        except AttributeError:
            self.assertTrue(expected in source)

    def assertDictContainsSubset(self, a, b, *args):
        try:
            DjangoTestCase.assertDictContainsSubset(self, a, b, *args)
        except AttributeError:
            for key, value in a.items():
                self.assertTrue(key in b)
                self.assertEqual(b[key], value)


class test_task_apply(ViewTestCase):

    def test_apply(self):
        current_app.conf.CELERY_ALWAYS_EAGER = True
        try:
            self.client.get(
                task_apply(kwargs={'task_name': mytask.name}) + '?x=4&y=4',
            )
            self.assertEqual(scratch['result'], 16)
        finally:
            current_app.conf.CELERY_ALWAYS_EAGER = False

    def test_apply_raises_404_on_unregistered_task(self):
        current_app.conf.CELERY_ALWAYS_EAGER = True
        try:
            name = 'xxx.does.not.exist'
            action = partial(
                self.client.get,
                task_apply(kwargs={'task_name': name}) + '?x=4&y=4',
            )
            try:
                res = action()
            except TemplateDoesNotExist:
                pass   # pre Django 1.5
            else:
                self.assertEqual(res.status_code, 404)
        finally:
            current_app.conf.CELERY_ALWAYS_EAGER = False


class test_registered_tasks(ViewTestCase):

    def test_list_registered_tasks(self):
        json = self.client.get(registered_tasks())
        tasks = deserialize(json.content)
        self.assertIn('celery.backend_cleanup', tasks['regular'])


class test_webhook_task(ViewTestCase):

    def test_successful_request(self):

        @task_webhook
        def add_webhook(request):
            x = int(request.GET['x'])
            y = int(request.GET['y'])
            return x + y

        request = MockRequest().get('/tasks/add', dict(x=10, y=10))
        response = add_webhook(request)
        self.assertDictContainsSubset({'status': 'success', 'retval': 20},
                                      deserialize(response.content))

    def test_failed_request(self):

        @task_webhook
        def error_webhook(request):
            x = int(request.GET['x'])
            y = int(request.GET['y'])
            raise MyError(x + y)

        request = MockRequest().get('/tasks/error', dict(x=10, y=10))
        response = error_webhook(request)
        self.assertDictContainsSubset({'status': 'failure',
                                       'reason': '<MyError: (20,)>'},
                                      deserialize(response.content))


class test_task_status(ViewTestCase):

    def assertStatusForIs(self, status, res, traceback=None):
        uuid = gen_unique_id()
        current_app.backend.store_result(uuid, res, status,
                                         traceback=traceback)
        json = self.client.get(task_status(task_id=uuid))
        expect = dict(id=uuid, status=status, result=res)
        if status in current_app.backend.EXCEPTION_STATES:
            instore = current_app.backend.get_result(uuid)
            self.assertEqual(str(instore.args[0]), str(res.args[0]))
            expect['result'] = repr(res)
            expect['exc'] = get_full_cls_name(res.__class__)
            expect['traceback'] = traceback

        self.assertJSONEqual(json, dict(task=expect))

    def test_success(self):
        self.assertStatusForIs(states.SUCCESS, 'The quick brown fox')

    def test_failure(self):
        exc, tb = catch_exception(MyError('foo'))
        self.assertStatusForIs(states.FAILURE, exc, tb)

    def test_retry(self):
        oexc, _ = catch_exception(MyError('Resource not available'))
        exc, tb = catch_exception(MyRetryTaskError(str(oexc), oexc))
        self.assertStatusForIs(states.RETRY, exc, tb)


class test_task_is_successful(ViewTestCase):

    def assertStatusForIs(self, status, outcome):
        uuid = gen_unique_id()
        result = gen_unique_id()
        current_app.backend.store_result(uuid, result, status)
        json = self.client.get(task_is_successful(task_id=uuid))
        self.assertJSONEqual(json, {'task': {'id': uuid,
                                             'executed': outcome}})

    def test_success(self):
        self.assertStatusForIs(states.SUCCESS, True)

    def test_pending(self):
        self.assertStatusForIs(states.PENDING, False)

    def test_failure(self):
        self.assertStatusForIs(states.FAILURE, False)

    def test_retry(self):
        self.assertStatusForIs(states.RETRY, False)
