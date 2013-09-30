"""
Compatibility support for Python 3.0. Remove when Python 3.0 support is
no longer required.
"""
import sys

if sys.version_info < (2,7) or sys.version_info[:2] == (3,0):
	import unittest2 as unittest
else:
	import unittest
