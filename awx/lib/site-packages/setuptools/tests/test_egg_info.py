import os
import sys
import tempfile
import shutil
import unittest

import pkg_resources
from setuptools.command import egg_info
from setuptools import svn_utils

ENTRIES_V10 = pkg_resources.resource_string(__name__, 'entries-v10')
"An entries file generated with svn 1.6.17 against the legacy Setuptools repo"

class TestEggInfo(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.test_dir, '.svn'))

        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def _write_entries(self, entries):
        fn = os.path.join(self.test_dir, '.svn', 'entries')
        entries_f = open(fn, 'wb')
        entries_f.write(entries)
        entries_f.close()

    def test_version_10_format(self):
        """
        """
        #keeping this set for 1.6 is a good check on the get_svn_revision
        #to ensure I return using svnversion what would had been returned
        version_str = svn_utils.SvnInfo.get_svn_version()
        version = [int(x) for x in version_str.split('.')[:2]]
        if version != [1,6]:
            if hasattr(self, 'skipTest'):
                self.skipTest('')
            else:
                sys.stderr.write('\n   Skipping due to SVN Version\n')
                return

        self._write_entries(ENTRIES_V10)
        rev = egg_info.egg_info.get_svn_revision()
        self.assertEqual(rev, '89000')

    def test_version_10_format_legacy_parser(self):
        """
        """
        path_variable = None
        for env in os.environ:
            if env.lower() == 'path':
                path_variable = env

        if path_variable is None:
            self.skipTest('Cannot figure out how to modify path')

        old_path = os.environ[path_variable]
        os.environ[path_variable] = ''
        try:
            self._write_entries(ENTRIES_V10)
            rev = egg_info.egg_info.get_svn_revision()
        finally:
            os.environ[path_variable] = old_path

        self.assertEqual(rev, '89000')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
