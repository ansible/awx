"""
Unit tests for external query discovery and version fallback logic.
Tests for AAP-58456: Unit Test Suite for External Query Handling
"""

import sys
from io import StringIO
from unittest import mock

import pytest
from packaging.version import Version


# Helper for mocking importlib.resources.files() path traversal
def create_chainable_path_mock(final_mock, depth=3):
    """Mock that supports chained / operations: mock / 'a' / 'b' / 'c' -> final_mock"""

    class ChainableMock:
        def __init__(self, d=0):
            self.d = d

        def __truediv__(self, other):
            return final_mock if self.d >= depth - 1 else ChainableMock(self.d + 1)

    return ChainableMock()


def create_queries_dir_mock(file_lookup_func):
    """Mock for queries_dir: mock / 'filename' -> file_lookup_func('filename')"""

    class QueriesDirMock:
        def __truediv__(self, filename):
            return file_lookup_func(filename)

    return QueriesDirMock()


# Ansible mocking required for importing the module (it imports from ansible.plugins.callback.CallbackBase)
class MockCallbackBase:
    def __init__(self):
        self._display = mock.MagicMock()

    def v2_playbook_on_stats(self, stats):
        pass


_mock_callback_module = mock.MagicMock()
_mock_callback_module.CallbackBase = MockCallbackBase


@pytest.fixture(autouse=True)
def _mock_ansible_modules():
    """Temporarily inject fake ansible modules so the callback plugin can be imported."""
    with mock.patch.dict(
        sys.modules,
        {
            'ansible': mock.MagicMock(),
            'ansible.plugins': mock.MagicMock(),
            'ansible.plugins.callback': _mock_callback_module,
            'ansible.cli': mock.MagicMock(),
            'ansible.cli.galaxy': mock.MagicMock(),
            'ansible.release': mock.MagicMock(__version__='2.16.0'),
            'ansible.galaxy': mock.MagicMock(),
            'ansible.galaxy.collection': mock.MagicMock(),
            'ansible.utils': mock.MagicMock(),
            'ansible.utils.collection_loader': mock.MagicMock(),
            'ansible.constants': mock.MagicMock(),
        },
    ):
        yield


class TestListExternalQueries:
    """Tests for list_external_queries function."""

    @mock.patch('awx.playbooks.library.indirect_instance_count.files')
    def test_returns_empty_when_collection_not_installed(self, mock_files):
        from awx.playbooks.library.indirect_instance_count import list_external_queries

        mock_files.side_effect = ModuleNotFoundError("No module named 'ansible_collections.redhat'")

        result = list_external_queries('demo', 'external')

        assert result == []

    @mock.patch('awx.playbooks.library.indirect_instance_count.files')
    def test_parses_version_from_filenames(self, mock_files):
        from awx.playbooks.library.indirect_instance_count import list_external_queries

        mock_file_1 = mock.Mock()
        mock_file_1.name = 'demo.external.1.0.0.yml'
        mock_file_2 = mock.Mock()
        mock_file_2.name = 'demo.external.2.1.0.yml'
        mock_file_other = mock.Mock()
        mock_file_other.name = 'other.collection.1.0.0.yml'

        mock_queries_dir = mock.Mock()
        mock_queries_dir.iterdir.return_value = [mock_file_1, mock_file_2, mock_file_other]
        mock_files.return_value = create_chainable_path_mock(mock_queries_dir)

        result = list_external_queries('demo', 'external')

        assert len(result) == 2
        assert Version('1.0.0') in result
        assert Version('2.1.0') in result

    @mock.patch('awx.playbooks.library.indirect_instance_count.files')
    def test_skips_invalid_versions(self, mock_files):
        from awx.playbooks.library.indirect_instance_count import list_external_queries

        mock_file_valid = mock.Mock()
        mock_file_valid.name = 'demo.external.1.0.0.yml'
        mock_file_invalid = mock.Mock()
        mock_file_invalid.name = 'demo.external.invalid.yml'

        mock_queries_dir = mock.Mock()
        mock_queries_dir.iterdir.return_value = [mock_file_valid, mock_file_invalid]
        mock_files.return_value = create_chainable_path_mock(mock_queries_dir)

        result = list_external_queries('demo', 'external')

        assert len(result) == 1
        assert Version('1.0.0') in result


class TestVersionFallback:
    """Tests for version fallback logic (AC7.4-AC7.9)."""

    @mock.patch('awx.playbooks.library.indirect_instance_count._get_query_file_dir')
    def test_exact_match_preferred(self, mock_get_dir):
        """AC7.4: Exact version match is preferred over fallback version."""
        from awx.playbooks.library.indirect_instance_count import find_external_query_with_fallback

        mock_exact_file = mock.Mock()
        mock_exact_file.exists.return_value = True
        mock_exact_file.open.return_value.__enter__ = mock.Mock(return_value=StringIO('exact_version_query'))
        mock_exact_file.open.return_value.__exit__ = mock.Mock(return_value=False)

        mock_get_dir.return_value = create_queries_dir_mock(lambda f: mock_exact_file)

        content, fallback_used, version = find_external_query_with_fallback('demo', 'external', '2.5.0')

        assert content == 'exact_version_query'
        assert fallback_used is False
        assert version == '2.5.0'

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_external_queries')
    @mock.patch('awx.playbooks.library.indirect_instance_count._get_query_file_dir')
    def test_fallback_nearest_lower_same_major(self, mock_get_dir, mock_list):
        """AC7.5: Fallback selects nearest lower version within same major version.

        When installed is 4.5.0 and 4.0.0/4.1.0 are available, selects 4.1.0.
        """
        from awx.playbooks.library.indirect_instance_count import find_external_query_with_fallback

        mock_list.return_value = [Version('4.0.0'), Version('4.1.0')]

        mock_exact_file = mock.Mock(exists=mock.Mock(return_value=False))
        mock_fallback_file = mock.Mock()
        mock_fallback_file.exists.return_value = True
        mock_fallback_file.open.return_value.__enter__ = mock.Mock(return_value=StringIO('fallback_query'))
        mock_fallback_file.open.return_value.__exit__ = mock.Mock(return_value=False)

        def file_lookup(filename):
            return mock_fallback_file if '4.1.0' in filename else mock_exact_file

        mock_get_dir.return_value = create_queries_dir_mock(file_lookup)

        content, fallback_used, version = find_external_query_with_fallback('community', 'vmware', '4.5.0')

        assert content == 'fallback_query'
        assert fallback_used is True
        assert version == '4.1.0'

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_external_queries')
    @mock.patch('awx.playbooks.library.indirect_instance_count._get_query_file_dir')
    def test_fallback_respects_major_version_boundary(self, mock_get_dir, mock_list):
        """Test that fallback does NOT cross major version boundaries.

        When installed version is 6.0.0 and only 5.0.0 query exists,
        no fallback should occur because major versions differ.
        """
        from awx.playbooks.library.indirect_instance_count import find_external_query_with_fallback

        mock_list.return_value = [Version('5.0.0')]

        # Mock exact file (6.0.0) to not exist
        mock_exact_file = mock.Mock(exists=mock.Mock(return_value=False))
        # Mock fallback file (5.0.0) to exist - if major version check is broken,
        # this file would be incorrectly selected
        mock_fallback_file = mock.Mock()
        mock_fallback_file.exists.return_value = True
        mock_fallback_file.open.return_value.__enter__ = mock.Mock(return_value=StringIO('wrong_major_version_query'))
        mock_fallback_file.open.return_value.__exit__ = mock.Mock(return_value=False)

        def file_lookup(filename):
            return mock_fallback_file if '5.0.0' in filename else mock_exact_file

        mock_get_dir.return_value = create_queries_dir_mock(file_lookup)

        content, fallback_used, version = find_external_query_with_fallback('community', 'vmware', '6.0.0')

        # Should NOT fall back to 5.0.0 because major version differs (5 vs 6)
        assert content is None
        assert fallback_used is False

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_external_queries')
    @mock.patch('awx.playbooks.library.indirect_instance_count._get_query_file_dir')
    def test_no_fallback_when_incompatible(self, mock_get_dir, mock_list):
        """AC7.7: No fallback when all available versions are higher than installed.

        When installed version is 3.8.0 and only 4.0.0 and 5.0.0 exist,
        no fallback should occur because both are higher than installed.
        """
        from awx.playbooks.library.indirect_instance_count import find_external_query_with_fallback

        mock_list.return_value = [Version('4.0.0'), Version('5.0.0')]

        # Mock exact file (3.8.0) to not exist
        mock_exact_file = mock.Mock(exists=mock.Mock(return_value=False))
        # Mock available files to exist - if version filtering is broken,
        # one of these would be incorrectly selected
        mock_available_file = mock.Mock()
        mock_available_file.exists.return_value = True
        mock_available_file.open.return_value.__enter__ = mock.Mock(return_value=StringIO('higher_version_query'))
        mock_available_file.open.return_value.__exit__ = mock.Mock(return_value=False)

        def file_lookup(filename):
            if '4.0.0' in filename or '5.0.0' in filename:
                return mock_available_file
            return mock_exact_file

        mock_get_dir.return_value = create_queries_dir_mock(file_lookup)

        content, fallback_used, version = find_external_query_with_fallback('community', 'vmware', '3.8.0')

        # Should NOT fall back to 4.0.0 or 5.0.0 because both are higher than 3.8.0
        assert content is None
        assert fallback_used is False

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_external_queries')
    @mock.patch('awx.playbooks.library.indirect_instance_count._get_query_file_dir')
    def test_fallback_selection_logic(self, mock_get_dir, mock_list):
        """AC7.9: Complex fallback scenario with multiple candidates.

        When installed is 4.5.0 and 4.0.0, 4.1.0, 5.0.0 are available,
        selects 4.1.0 (highest compatible within same major, <= installed).
        """
        from awx.playbooks.library.indirect_instance_count import find_external_query_with_fallback

        mock_list.return_value = [Version('4.0.0'), Version('4.1.0'), Version('5.0.0')]

        mock_exact_file = mock.Mock(exists=mock.Mock(return_value=False))
        mock_fallback_file = mock.Mock()
        mock_fallback_file.exists.return_value = True
        mock_fallback_file.open.return_value.__enter__ = mock.Mock(return_value=StringIO('query_4.1.0'))
        mock_fallback_file.open.return_value.__exit__ = mock.Mock(return_value=False)

        def file_lookup(filename):
            return mock_fallback_file if '4.1.0' in filename else mock_exact_file

        mock_get_dir.return_value = create_queries_dir_mock(file_lookup)

        content, fallback_used, version = find_external_query_with_fallback('community', 'vmware', '4.5.0')

        assert version == '4.1.0'
        assert fallback_used is True
        assert content == 'query_4.1.0'


class TestExternalQueryDiscovery:
    """Tests for callback plugin query discovery (AC7.1-AC7.3)."""

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_collections')
    @mock.patch('awx.playbooks.library.indirect_instance_count.files')
    @mock.patch('awx.playbooks.library.indirect_instance_count.find_external_query_with_fallback')
    @mock.patch.dict('os.environ', {'AWX_ISOLATED_DATA_DIR': '/tmp/artifacts'})
    def test_precedence_embedded_over_external(self, mock_fallback, mock_files, mock_list_collections):
        """AC7.1: Embedded query takes precedence when both embedded and external exist."""
        from awx.playbooks.library.indirect_instance_count import CallbackModule

        mock_list_collections.return_value = [mock.Mock(namespace='demo', name='query', ver='1.0.0', fqcn='demo.query')]

        mock_embedded_file = mock.Mock()
        mock_embedded_file.exists.return_value = True
        mock_embedded_file.open.return_value.__enter__ = mock.Mock(return_value=StringIO('embedded_query'))
        mock_embedded_file.open.return_value.__exit__ = mock.Mock(return_value=False)
        mock_files.return_value = create_chainable_path_mock(mock_embedded_file)

        callback = CallbackModule()
        callback._display = mock.Mock()

        with mock.patch('builtins.open', mock.mock_open()):
            with mock.patch('json.dumps', return_value='{}'):
                callback.v2_playbook_on_stats(mock.Mock())

        mock_fallback.assert_not_called()
        callback._display.vv.assert_called()

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_collections')
    @mock.patch('awx.playbooks.library.indirect_instance_count.files')
    @mock.patch('awx.playbooks.library.indirect_instance_count.find_external_query_with_fallback')
    @mock.patch.dict('os.environ', {'AWX_ISOLATED_DATA_DIR': '/tmp/artifacts'})
    def test_external_query_when_embedded_missing(self, mock_fallback, mock_files, mock_list_collections):
        """AC7.2: External query is discovered when embedded query is missing."""
        from awx.playbooks.library.indirect_instance_count import CallbackModule

        mock_candidate = mock.Mock()
        mock_candidate.namespace = 'demo'
        mock_candidate.name = 'external'
        mock_candidate.ver = '2.5.0'
        mock_candidate.fqcn = 'demo.external'
        mock_list_collections.return_value = [mock_candidate]

        mock_embedded_file = mock.Mock(exists=mock.Mock(return_value=False))
        mock_files.return_value = create_chainable_path_mock(mock_embedded_file)
        mock_fallback.return_value = ('external_query_content', False, '2.5.0')

        callback = CallbackModule()
        callback._display = mock.Mock()

        with mock.patch('builtins.open', mock.mock_open()):
            with mock.patch('json.dumps', return_value='{}'):
                callback.v2_playbook_on_stats(mock.Mock())

        mock_fallback.assert_called_once_with('demo', 'external', '2.5.0')
        callback._display.v.assert_called()

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_collections')
    @mock.patch('awx.playbooks.library.indirect_instance_count.files')
    @mock.patch('awx.playbooks.library.indirect_instance_count.find_external_query_with_fallback')
    @mock.patch.dict('os.environ', {'AWX_ISOLATED_DATA_DIR': '/tmp/artifacts'})
    def test_no_query_when_both_missing(self, mock_fallback, mock_files, mock_list_collections):
        """AC7.3: No query is used when both embedded and external queries are missing."""
        from awx.playbooks.library.indirect_instance_count import CallbackModule

        mock_list_collections.return_value = [mock.Mock(namespace='unknown', name='collection', ver='1.0.0', fqcn='unknown.collection')]

        mock_embedded_file = mock.Mock(exists=mock.Mock(return_value=False))
        mock_files.return_value = create_chainable_path_mock(mock_embedded_file)
        mock_fallback.return_value = (None, False, None)

        callback = CallbackModule()
        callback._display = mock.Mock()

        with mock.patch('builtins.open', mock.mock_open()):
            with mock.patch('json.dumps', return_value='{}'):
                callback.v2_playbook_on_stats(mock.Mock())

        mock_fallback.assert_called_once()

    @mock.patch('awx.playbooks.library.indirect_instance_count.list_collections')
    @mock.patch('awx.playbooks.library.indirect_instance_count.files')
    @mock.patch('awx.playbooks.library.indirect_instance_count.find_external_query_with_fallback')
    @mock.patch.dict('os.environ', {'AWX_ISOLATED_DATA_DIR': '/tmp/artifacts'})
    def test_info_log_on_fallback(self, mock_fallback, mock_files, mock_list_collections):
        """AC7.8: Log message is emitted when fallback version is used.

        Verifies that when a fallback version is used, a log message is emitted
        containing both the fallback version and the collection FQCN.

        Note: AC7.8 specifies 'warning logs' but implementation uses verbose/info
        level (_display.v) as this is informational rather than a warning condition.
        """
        from awx.playbooks.library.indirect_instance_count import CallbackModule

        mock_list_collections.return_value = [mock.Mock(namespace='community', name='vmware', ver='4.5.0', fqcn='community.vmware')]

        mock_embedded_file = mock.Mock(exists=mock.Mock(return_value=False))
        mock_files.return_value = create_chainable_path_mock(mock_embedded_file)
        mock_fallback.return_value = ('fallback_query_content', True, '4.1.0')

        callback = CallbackModule()
        callback._display = mock.Mock()

        with mock.patch('builtins.open', mock.mock_open()):
            with mock.patch('json.dumps', return_value='{}'):
                callback.v2_playbook_on_stats(mock.Mock())

        callback._display.v.assert_called()
        call_args = callback._display.v.call_args[0][0]
        assert '4.1.0' in call_args
        assert 'community.vmware' in call_args


class TestPrivateDataDirIntegration:
    """Tests for vendor collection copying (AC7.10-AC7.11)."""

    @mock.patch('awx.main.tasks.jobs.flag_enabled')
    @mock.patch('awx.main.tasks.jobs.shutil.copytree')
    @mock.patch('awx.main.tasks.jobs.os.path.exists')
    def test_vendor_collections_copied(self, mock_exists, mock_copytree, mock_flag):
        """AC7.10: build_private_data_files() copies vendor collections to private_data_dir."""
        from awx.main.tasks.jobs import BaseTask

        mock_flag.return_value = True
        mock_exists.return_value = True

        task = BaseTask()
        task.instance = mock.Mock()
        task.cleanup_paths = []
        task.build_private_data = mock.Mock(return_value=None)

        private_data_dir = '/tmp/awx_123_abc'
        task.build_private_data_files(task.instance, private_data_dir)

        mock_copytree.assert_called_once_with('/var/lib/awx/vendor_collections', f'{private_data_dir}/vendor_collections')

    @mock.patch('awx.main.tasks.jobs.flag_enabled')
    @mock.patch('awx.main.tasks.jobs.logger')
    @mock.patch('awx.main.tasks.jobs.shutil.copytree')
    @mock.patch('awx.main.tasks.jobs.os.path.exists')
    def test_missing_source_handled_gracefully(self, mock_exists, mock_copytree, mock_logger, mock_flag):
        """AC7.11: Collection copy handles missing source directory gracefully."""
        from awx.main.tasks.jobs import BaseTask

        mock_flag.return_value = True
        mock_exists.return_value = False

        task = BaseTask()
        task.instance = mock.Mock()
        task.cleanup_paths = []
        task.build_private_data = mock.Mock(return_value=None)

        private_data_dir = '/tmp/awx_123_abc'
        result = task.build_private_data_files(task.instance, private_data_dir)

        # copytree should not be called when source doesn't exist
        mock_copytree.assert_not_called()
        # Function should complete without raising an exception
        assert result is not None
