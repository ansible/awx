"""Tests for stevedore.exmaple.fields
"""

from stevedore.example import fields
from stevedore.tests import utils


class TestExampleFields(utils.TestCase):
    def test_simple_items(self):
        f = fields.FieldList(100)
        text = ''.join(f.format({'a': 'A', 'b': 'B'}))
        expected = '\n'.join([
            ': a : A',
            ': b : B',
            '',
        ])
        self.assertEqual(text, expected)

    def test_long_item(self):
        f = fields.FieldList(25)
        text = ''.join(f.format({'name':
                       'a value longer than the allowed width'}))
        expected = '\n'.join([
            ': name : a value longer',
            '    than the allowed',
            '    width',
            '',
        ])
        self.assertEqual(text, expected)
