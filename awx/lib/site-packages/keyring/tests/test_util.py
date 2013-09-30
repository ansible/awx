# -*- coding: utf-8 -*-

"""
Test for simple escape/unescape routine
"""


from .py30compat import unittest

from keyring.util import escape


class EscapeTestCase(unittest.TestCase):

    def check_escape_unescape(self, initial):
        escaped = escape.escape(initial)
        self.assertTrue(all(c in (escape.LEGAL_CHARS + '_') for c in escaped))
        unescaped = escape.unescape(escaped)
        self.assertEqual(initial, unescaped)

    def test_escape_unescape(self):
        self.check_escape_unescape("aaaa")
        self.check_escape_unescape("aaaa bbbb cccc")
        self.check_escape_unescape(escape.u("Zażółć gęślą jaźń"))
        self.check_escape_unescape("(((P{{{{'''---; ;; '\"|%^")

    def test_low_byte(self):
        """
        Ensure that encoding low bytes (ordinal less than hex F) encode as
        as three bytes to avoid ambiguity. For example '\n' (hex A) should
        encode as '_0A' and not '_A', the latter of which
        isn't matched by the inverse operation.
        """
        self.check_escape_unescape('\n')
        self.check_escape_unescape('\x000')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(EscapeTestCase))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
