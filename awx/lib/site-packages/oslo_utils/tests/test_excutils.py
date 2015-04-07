# Copyright 2012, Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import time

import mock
from oslotest import base as test_base
from oslotest import moxstubout

from oslo_utils import excutils


mox = moxstubout.mox


class SaveAndReraiseTest(test_base.BaseTestCase):

    def test_save_and_reraise_exception(self):
        e = None
        msg = 'foo'
        try:
            try:
                raise Exception(msg)
            except Exception:
                with excutils.save_and_reraise_exception():
                    pass
        except Exception as _e:
            e = _e

        self.assertEqual(str(e), msg)

    @mock.patch('logging.getLogger')
    def test_save_and_reraise_exception_dropped(self, get_logger_mock):
        logger = get_logger_mock()
        e = None
        msg = 'second exception'
        try:
            try:
                raise Exception('dropped')
            except Exception:
                with excutils.save_and_reraise_exception():
                    raise Exception(msg)
        except Exception as _e:
            e = _e
        self.assertEqual(str(e), msg)
        self.assertTrue(logger.error.called)

    def test_save_and_reraise_exception_no_reraise(self):
        """Test that suppressing the reraise works."""
        try:
            raise Exception('foo')
        except Exception:
            with excutils.save_and_reraise_exception() as ctxt:
                ctxt.reraise = False

    @mock.patch('logging.getLogger')
    def test_save_and_reraise_exception_dropped_no_reraise(self,
                                                           get_logger_mock):
        logger = get_logger_mock()
        e = None
        msg = 'second exception'
        try:
            try:
                raise Exception('dropped')
            except Exception:
                with excutils.save_and_reraise_exception(reraise=False):
                    raise Exception(msg)
        except Exception as _e:
            e = _e
        self.assertEqual(str(e), msg)
        self.assertFalse(logger.error.called)

    def test_save_and_reraise_exception_provided_logger(self):
        fake_logger = mock.MagicMock()
        try:
            try:
                raise Exception('foo')
            except Exception:
                with excutils.save_and_reraise_exception(logger=fake_logger):
                    raise Exception('second exception')
        except Exception:
            pass
        self.assertTrue(fake_logger.error.called)


class ForeverRetryUncaughtExceptionsTest(test_base.BaseTestCase):

    def setUp(self):
        super(ForeverRetryUncaughtExceptionsTest, self).setUp()
        moxfixture = self.useFixture(moxstubout.MoxStubout())
        self.mox = moxfixture.mox
        self.stubs = moxfixture.stubs

    @excutils.forever_retry_uncaught_exceptions
    def exception_generator(self):
        exc = self.exception_to_raise()
        while exc is not None:
            raise exc
            exc = self.exception_to_raise()

    def exception_to_raise(self):
        return None

    def my_time_sleep(self, arg):
        pass

    def exc_retrier_common_start(self):
        self.stubs.Set(time, 'sleep', self.my_time_sleep)
        self.mox.StubOutWithMock(logging, 'exception')
        self.mox.StubOutWithMock(time, 'time',
                                 use_mock_anything=True)
        self.mox.StubOutWithMock(self, 'exception_to_raise')

    def exc_retrier_sequence(self, exc_id=None, timestamp=None,
                             exc_count=None):
        self.exception_to_raise().AndReturn(
            Exception('unexpected %d' % exc_id))
        time.time().AndReturn(timestamp)
        if exc_count != 0:
            logging.exception(mox.In(
                'Unexpected exception occurred %d time(s)' % exc_count))

    def exc_retrier_common_end(self):
        self.exception_to_raise().AndReturn(None)
        self.mox.ReplayAll()
        self.exception_generator()
        self.addCleanup(self.stubs.UnsetAll)

    def test_exc_retrier_1exc_gives_1log(self):
        self.exc_retrier_common_start()
        self.exc_retrier_sequence(exc_id=1, timestamp=1, exc_count=1)
        self.exc_retrier_common_end()

    def test_exc_retrier_same_10exc_1min_gives_1log(self):
        self.exc_retrier_common_start()
        self.exc_retrier_sequence(exc_id=1, timestamp=1, exc_count=1)
        # By design, the following exception don't get logged because they
        # are within the same minute.
        for i in range(2, 11):
            self.exc_retrier_sequence(exc_id=1, timestamp=i, exc_count=0)
        self.exc_retrier_common_end()

    def test_exc_retrier_same_2exc_2min_gives_2logs(self):
        self.exc_retrier_common_start()
        self.exc_retrier_sequence(exc_id=1, timestamp=1, exc_count=1)
        self.exc_retrier_sequence(exc_id=1, timestamp=65, exc_count=1)
        self.exc_retrier_common_end()

    def test_exc_retrier_same_10exc_2min_gives_2logs(self):
        self.exc_retrier_common_start()
        self.exc_retrier_sequence(exc_id=1, timestamp=1, exc_count=1)
        self.exc_retrier_sequence(exc_id=1, timestamp=12, exc_count=0)
        self.exc_retrier_sequence(exc_id=1, timestamp=23, exc_count=0)
        self.exc_retrier_sequence(exc_id=1, timestamp=34, exc_count=0)
        self.exc_retrier_sequence(exc_id=1, timestamp=45, exc_count=0)
        # The previous 4 exceptions are counted here
        self.exc_retrier_sequence(exc_id=1, timestamp=106, exc_count=5)
        # Again, the following are not logged due to being within
        # the same minute
        self.exc_retrier_sequence(exc_id=1, timestamp=117, exc_count=0)
        self.exc_retrier_sequence(exc_id=1, timestamp=128, exc_count=0)
        self.exc_retrier_sequence(exc_id=1, timestamp=139, exc_count=0)
        self.exc_retrier_sequence(exc_id=1, timestamp=150, exc_count=0)
        self.exc_retrier_common_end()

    def test_exc_retrier_mixed_4exc_1min_gives_2logs(self):
        self.exc_retrier_common_start()
        self.exc_retrier_sequence(exc_id=1, timestamp=1, exc_count=1)
        # By design, this second 'unexpected 1' exception is not counted.  This
        # is likely a rare thing and is a sacrifice for code simplicity.
        self.exc_retrier_sequence(exc_id=1, timestamp=10, exc_count=0)
        self.exc_retrier_sequence(exc_id=2, timestamp=20, exc_count=1)
        # Again, trailing exceptions within a minute are not counted.
        self.exc_retrier_sequence(exc_id=2, timestamp=30, exc_count=0)
        self.exc_retrier_common_end()

    def test_exc_retrier_mixed_4exc_2min_gives_2logs(self):
        self.exc_retrier_common_start()
        self.exc_retrier_sequence(exc_id=1, timestamp=1, exc_count=1)
        # Again, this second exception of the same type is not counted
        # for the sake of code simplicity.
        self.exc_retrier_sequence(exc_id=1, timestamp=10, exc_count=0)
        # The difference between this and the previous case is the log
        # is also triggered by more than a minute expiring.
        self.exc_retrier_sequence(exc_id=2, timestamp=100, exc_count=1)
        self.exc_retrier_sequence(exc_id=2, timestamp=110, exc_count=0)
        self.exc_retrier_common_end()

    def test_exc_retrier_mixed_4exc_2min_gives_3logs(self):
        self.exc_retrier_common_start()
        self.exc_retrier_sequence(exc_id=1, timestamp=1, exc_count=1)
        # This time the second 'unexpected 1' exception is counted due
        # to the same exception occurring same when the minute expires.
        self.exc_retrier_sequence(exc_id=1, timestamp=10, exc_count=0)
        self.exc_retrier_sequence(exc_id=1, timestamp=100, exc_count=2)
        self.exc_retrier_sequence(exc_id=2, timestamp=110, exc_count=1)
        self.exc_retrier_common_end()
