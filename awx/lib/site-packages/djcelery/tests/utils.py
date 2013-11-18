from __future__ import absolute_import, unicode_literals

try:
    import unittest
    unittest.skip
except AttributeError:
    import unittest2 as unittest  # noqa
