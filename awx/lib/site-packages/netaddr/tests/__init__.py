#!/usr/bin/env python
#-----------------------------------------------------------------------------
#   Copyright (c) 2008-2015, David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
#-----------------------------------------------------------------------------
"""Runs all netaddr unit tests."""

from os.path import abspath, basename, dirname, join as pathjoin
import sys
import glob
import doctest
import unittest

sys.path.insert(0, abspath(pathjoin(dirname(__file__), '..', '..')))


def test_suite_all():

    test_dirs = [
        'ip',
        'eui',
        'strategy',
        'core'
    ]

    base_path = abspath(pathjoin(dirname(__file__), '..'))

    #   Select tests based on the version of the Python interpreter.
    py_ver_dir = '2.x'
    if sys.version_info[0] == 3:
        py_ver_dir = '3.x'

    #   Gather list of files containing tests.
    test_files = []
    for entry in test_dirs:
        test_path = pathjoin(base_path, "tests", py_ver_dir, entry, "*.txt")
        files = glob.glob(test_path)
        test_files.extend(files)

    sys.stdout.write('testdir: %s\n' % '\n'.join(test_files))

    #   Add anything to the skiplist that we want to leave out.
    skiplist = []

    #   Drop platform specific tests for other platforms.
    platform_tests = ['platform_darwin.txt', 'platform_linux2.txt', 'platform_win32.txt']
    for platform_test in platform_tests:
        if not sys.platform in platform_test:
            skiplist.append(platform_test)

    #   Exclude any entries from the skip list.
    test_files = [t for t in test_files if basename(t) not in skiplist]

    #   Build and return a complete unittest test suite.
    suite = unittest.TestSuite()

    for test_file in test_files:
        doctest_suite = doctest.DocFileSuite(test_file,
            optionflags=doctest.ELLIPSIS, module_relative=False)
        suite.addTest(doctest_suite)

    return suite


def run():
    runner = unittest.TextTestRunner()
    return runner.run(test_suite_all())


if __name__ == "__main__":
    result = run()
    sys.exit(not result.wasSuccessful())
