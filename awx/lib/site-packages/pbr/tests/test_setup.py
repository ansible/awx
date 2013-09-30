# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function

import os
import sys
import tempfile

try:
    import cStringIO as io
    BytesIO = io.StringIO
except ImportError:
    import io
    BytesIO = io.BytesIO

import fixtures
import testscenarios

from pbr import packaging
from pbr import tests


class EmailTestCase(tests.BaseTestCase):

    def test_str_dict_replace(self):
        string = 'Johnnie T. Hozer'
        mapping = {'T.': 'The'}
        self.assertEqual('Johnnie The Hozer',
                         packaging.canonicalize_emails(string, mapping))


class MailmapTestCase(tests.BaseTestCase):

    def setUp(self):
        super(MailmapTestCase, self).setUp()
        self.root_dir = self.useFixture(fixtures.TempDir()).path
        self.mailmap = os.path.join(self.root_dir, '.mailmap')

    def test_mailmap_with_fullname(self):
        with open(self.mailmap, 'w') as mm_fh:
            mm_fh.write("Foo Bar <email@foo.com> Foo Bar <email@bar.com>\n")
        self.assertEqual({'<email@bar.com>': '<email@foo.com>'},
                         packaging.read_git_mailmap(self.root_dir))

    def test_mailmap_with_firstname(self):
        with open(self.mailmap, 'w') as mm_fh:
            mm_fh.write("Foo <email@foo.com> Foo <email@bar.com>\n")
        self.assertEqual({'<email@bar.com>': '<email@foo.com>'},
                         packaging.read_git_mailmap(self.root_dir))

    def test_mailmap_with_noname(self):
        with open(self.mailmap, 'w') as mm_fh:
            mm_fh.write("<email@foo.com> <email@bar.com>\n")
        self.assertEqual({'<email@bar.com>': '<email@foo.com>'},
                         packaging.read_git_mailmap(self.root_dir))


class SkipFileWrites(tests.BaseTestCase):

    scenarios = [
        ('changelog_option_true',
         dict(option_key='skip_changelog', option_value='True',
              env_key='SKIP_WRITE_GIT_CHANGELOG', env_value=None,
              pkg_func=packaging.write_git_changelog, filename='ChangeLog')),
        ('changelog_option_false',
         dict(option_key='skip_changelog', option_value='False',
              env_key='SKIP_WRITE_GIT_CHANGELOG', env_value=None,
              pkg_func=packaging.write_git_changelog, filename='ChangeLog')),
        ('changelog_env_true',
         dict(option_key='skip_changelog', option_value='False',
              env_key='SKIP_WRITE_GIT_CHANGELOG', env_value='True',
              pkg_func=packaging.write_git_changelog, filename='ChangeLog')),
        ('changelog_both_true',
         dict(option_key='skip_changelog', option_value='True',
              env_key='SKIP_WRITE_GIT_CHANGELOG', env_value='True',
              pkg_func=packaging.write_git_changelog, filename='ChangeLog')),
        ('authors_option_true',
         dict(option_key='skip_authors', option_value='True',
              env_key='SKIP_GENERATE_AUTHORS', env_value=None,
              pkg_func=packaging.generate_authors, filename='AUTHORS')),
        ('authors_option_false',
         dict(option_key='skip_authors', option_value='False',
              env_key='SKIP_GENERATE_AUTHORS', env_value=None,
              pkg_func=packaging.generate_authors, filename='AUTHORS')),
        ('authors_env_true',
         dict(option_key='skip_authors', option_value='False',
              env_key='SKIP_GENERATE_AUTHORS', env_value='True',
              pkg_func=packaging.generate_authors, filename='AUTHORS')),
        ('authors_both_true',
         dict(option_key='skip_authors', option_value='True',
              env_key='SKIP_GENERATE_AUTHORS', env_value='True',
              pkg_func=packaging.generate_authors, filename='AUTHORS')),
    ]

    def setUp(self):
        super(SkipFileWrites, self).setUp()
        self.temp_path = self.useFixture(fixtures.TempDir()).path
        self.root_dir = os.path.abspath(os.path.curdir)
        self.git_dir = os.path.join(self.root_dir, ".git")
        if not os.path.exists(self.git_dir):
            self.skipTest("%s is missing; skipping git-related checks"
                          % self.git_dir)
            return
        self.filename = os.path.join(self.temp_path, self.filename)
        self.option_dict = dict()
        if self.option_key is not None:
            self.option_dict[self.option_key] = ('setup.cfg',
                                                 self.option_value)
        self.useFixture(
            fixtures.EnvironmentVariable(self.env_key, self.env_value))

    def test_skip(self):
        self.pkg_func(git_dir=self.git_dir,
                      dest_dir=self.temp_path,
                      option_dict=self.option_dict)
        self.assertEqual(
            not os.path.exists(self.filename),
            (self.option_value.lower() in packaging.TRUE_VALUES
             or self.env_value is not None))


class GitLogsTest(tests.BaseTestCase):

    def setUp(self):
        super(GitLogsTest, self).setUp()
        self.temp_path = self.useFixture(fixtures.TempDir()).path
        self.root_dir = os.path.abspath(os.path.curdir)
        self.git_dir = os.path.join(self.root_dir, ".git")
        self.useFixture(
            fixtures.EnvironmentVariable('SKIP_GENERATE_AUTHORS'))
        self.useFixture(
            fixtures.EnvironmentVariable('SKIP_WRITE_GIT_CHANGELOG'))

    def test_write_git_changelog(self):
        exist_files = [os.path.join(self.root_dir, f)
                       for f in (".git", ".mailmap")]
        self.useFixture(fixtures.MonkeyPatch(
            "os.path.exists",
            lambda path: os.path.abspath(path) in exist_files))
        self.useFixture(fixtures.FakePopen(lambda _: {
            "stdout": BytesIO("Author: Foo Bar "
                              "<email@bar.com>\n".encode('utf-8'))
        }))

        def _fake_read_git_mailmap(*args):
            return {"email@bar.com": "email@foo.com"}

        self.useFixture(fixtures.MonkeyPatch("pbr.packaging.read_git_mailmap",
                                             _fake_read_git_mailmap))

        packaging.write_git_changelog(git_dir=self.git_dir,
                                      dest_dir=self.temp_path)

        with open(os.path.join(self.temp_path, "ChangeLog"), "r") as ch_fh:
            self.assertTrue("email@foo.com" in ch_fh.read())

    def _fake_log_output(self, cmd, mapping):
        for (k, v) in mapping.items():
            if cmd.startswith(k):
                return v.encode('utf-8')
        return b""

    def test_generate_authors(self):
        author_old = "Foo Foo <email@foo.com>"
        author_new = "Bar Bar <email@bar.com>"
        co_author = "Foo Bar <foo@bar.com>"
        co_author_by = "Co-authored-by: " + co_author

        git_log_cmd = ("git --git-dir=%s log --format" % self.git_dir)
        git_co_log_cmd = ("git log --git-dir=%s" % self.git_dir)
        git_top_level = "git rev-parse --show-toplevel"
        cmd_map = {
            git_log_cmd: author_new,
            git_co_log_cmd: co_author_by,
            git_top_level: self.root_dir,
        }

        exist_files = [self.git_dir,
                       os.path.join(self.temp_path, "AUTHORS.in")]
        self.useFixture(fixtures.MonkeyPatch(
            "os.path.exists",
            lambda path: os.path.abspath(path) in exist_files))

        self.useFixture(fixtures.FakePopen(lambda proc_args: {
            "stdout": BytesIO(
                self._fake_log_output(proc_args["args"][2], cmd_map))
        }))

        with open(os.path.join(self.temp_path, "AUTHORS.in"), "w") as auth_fh:
            auth_fh.write("%s\n" % author_old)

        packaging.generate_authors(git_dir=self.git_dir,
                                   dest_dir=self.temp_path)

        with open(os.path.join(self.temp_path, "AUTHORS"), "r") as auth_fh:
            authors = auth_fh.read()
            self.assertTrue(author_old in authors)
            self.assertTrue(author_new in authors)
            self.assertTrue(co_author in authors)


class BuildSphinxTest(tests.BaseTestCase):

    scenarios = [
        ('true_autodoc_caps',
         dict(has_opt=True, autodoc='True', has_autodoc=True)),
        ('true_autodoc_lower',
         dict(has_opt=True, autodoc='true', has_autodoc=True)),
        ('false_autodoc',
         dict(has_opt=True, autodoc='False', has_autodoc=False)),
        ('no_autodoc',
         dict(has_opt=False, autodoc='False', has_autodoc=False)),
    ]

    def setUp(self):
        super(BuildSphinxTest, self).setUp()

        self.useFixture(fixtures.MonkeyPatch(
            "sphinx.setup_command.BuildDoc.run", lambda self: None))
        from distutils import dist
        self.distr = dist.Distribution()
        self.distr.packages = ("fake_package",)
        self.distr.command_options["build_sphinx"] = {
            "source_dir": ["a", "."]}
        pkg_fixture = fixtures.PythonPackage(
            "fake_package", [("fake_module.py", b"")])
        self.useFixture(pkg_fixture)
        self.useFixture(tests.DiveDir(pkg_fixture.base))

    def test_build_doc(self):
        if self.has_opt:
            self.distr.command_options["pbr"] = {
                "autodoc_index_modules": ('setup.cfg', self.autodoc)}
        build_doc = packaging.LocalBuildDoc(self.distr)
        build_doc.run()

        self.assertTrue(
            os.path.exists("api/autoindex.rst") == self.has_autodoc)
        self.assertTrue(
            os.path.exists(
                "api/fake_package.fake_module.rst") == self.has_autodoc)


class ParseRequirementsTest(tests.BaseTestCase):

    def setUp(self):
        super(ParseRequirementsTest, self).setUp()
        (fd, self.tmp_file) = tempfile.mkstemp(prefix='openstack',
                                               suffix='.setup')

    def test_parse_requirements_normal(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("foo\nbar")
        self.assertEqual(['foo', 'bar'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_with_git_egg_url(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("-e git://foo.com/zipball#egg=bar")
        self.assertEqual(['bar'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_with_versioned_git_egg_url(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("-e git://foo.com/zipball#egg=bar-1.2.4")
        self.assertEqual(['bar>=1.2.4'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_with_http_egg_url(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("https://foo.com/zipball#egg=bar")
        self.assertEqual(['bar'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_with_versioned_http_egg_url(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("https://foo.com/zipball#egg=bar-4.2.1")
        self.assertEqual(['bar>=4.2.1'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_removes_index_lines(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("-f foobar")
        self.assertEqual([], packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_removes_argparse(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("argparse")
        if sys.version_info >= (2, 7):
            self.assertEqual([], packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_override_with_env(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("foo\nbar")
        self.useFixture(
            fixtures.EnvironmentVariable('PBR_REQUIREMENTS_FILES',
                                         self.tmp_file))
        self.assertEqual(['foo', 'bar'],
                         packaging.parse_requirements())

    def test_parse_requirements_override_with_env_multiple_files(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("foo\nbar")
        self.useFixture(
            fixtures.EnvironmentVariable('PBR_REQUIREMENTS_FILES',
                                         "no-such-file," + self.tmp_file))
        self.assertEqual(['foo', 'bar'],
                         packaging.parse_requirements())

    def test_get_requirement_from_file_empty(self):
        actual = packaging.get_reqs_from_files([])
        self.assertEqual([], actual)

    def test_parse_requirements_with_comments(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("# this is a comment\nfoobar\n# and another one\nfoobaz")
        self.assertEqual(['foobar', 'foobaz'],
                         packaging.parse_requirements([self.tmp_file]))


class ParseDependencyLinksTest(tests.BaseTestCase):

    def setUp(self):
        super(ParseDependencyLinksTest, self).setUp()
        (fd, self.tmp_file) = tempfile.mkstemp(prefix="openstack",
                                               suffix=".setup")

    def test_parse_dependency_normal(self):
        with open(self.tmp_file, "w") as fh:
            fh.write("http://test.com\n")
        self.assertEqual(
            ["http://test.com"],
            packaging.parse_dependency_links([self.tmp_file]))

    def test_parse_dependency_with_git_egg_url(self):
        with open(self.tmp_file, "w") as fh:
            fh.write("-e git://foo.com/zipball#egg=bar")
        self.assertEqual(
            ["git://foo.com/zipball#egg=bar"],
            packaging.parse_dependency_links([self.tmp_file]))


def load_tests(loader, in_tests, pattern):
    return testscenarios.load_tests_apply_scenarios(loader, in_tests, pattern)
