from __future__ import absolute_import

import pickle

from kombu.utils.functional import promise, maybe_promise

from kombu.tests.utils import TestCase


def double(x):
    return x * 2


class test_promise(TestCase):

    def test__str__(self):
        self.assertEqual(
            str(promise(lambda: 'the quick brown fox')),
            'the quick brown fox',
        )

    def test__repr__(self):
        self.assertEqual(
            repr(promise(lambda: 'fi fa fo')),
            "'fi fa fo'",
        )

    def test_evaluate(self):
        self.assertEqual(promise(lambda: 2 + 2)(), 4)
        self.assertEqual(promise(lambda x: x * 4, 2), 8)
        self.assertEqual(promise(lambda x: x * 8, 2)(), 16)

    def test_cmp(self):
        self.assertEqual(promise(lambda: 10), promise(lambda: 10))
        self.assertNotEqual(promise(lambda: 10), promise(lambda: 20))

    def test__reduce__(self):
        x = promise(double, 4)
        y = pickle.loads(pickle.dumps(x))
        self.assertEqual(x(), y())

    def test__deepcopy__(self):
        from copy import deepcopy
        x = promise(double, 4)
        y = deepcopy(x)
        self.assertEqual(x._fun, y._fun)
        self.assertEqual(x._args, y._args)
        self.assertEqual(x(), y())


class test_maybe_promise(TestCase):

    def test_evaluates(self):
        self.assertEqual(maybe_promise(promise(lambda: 10)), 10)
        self.assertEqual(maybe_promise(20), 20)
