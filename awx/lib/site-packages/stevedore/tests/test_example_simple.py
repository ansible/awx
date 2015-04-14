"""Tests for stevedore.exmaple.simple
"""

from stevedore.example import simple
from stevedore.tests import utils


class TestExampleSimple(utils.TestCase):
    def test_simple_items(self):
        f = simple.Simple(100)
        text = ''.join(f.format({'a': 'A', 'b': 'B'}))
        expected = '\n'.join([
            'a = A',
            'b = B',
            '',
        ])
        self.assertEqual(text, expected)
