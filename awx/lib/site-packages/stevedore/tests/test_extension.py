"""Tests for stevedore.extension
"""

import mock

from stevedore import extension
from stevedore.tests import utils


ALL_NAMES = ['e1', 't1', 't2']
WORKING_NAMES = ['t1', 't2']


class FauxExtension(object):
    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds

    def get_args_and_data(self, data):
        return self.args, self.kwds, data


class BrokenExtension(object):
    def __init__(self, *args, **kwds):
        raise IOError("Did not create")


class TestCallback(utils.TestCase):
    def test_detect_plugins(self):
        em = extension.ExtensionManager('stevedore.test.extension')
        names = sorted(em.names())
        self.assertEqual(names, ALL_NAMES)

    def test_get_by_name(self):
        em = extension.ExtensionManager('stevedore.test.extension')
        e = em['t1']
        self.assertEqual(e.name, 't1')

    def test_contains_by_name(self):
        em = extension.ExtensionManager('stevedore.test.extension')
        self.assertEqual('t1' in em, True)

    def test_get_by_name_missing(self):
        em = extension.ExtensionManager('stevedore.test.extension')
        try:
            em['t3']
        except KeyError:
            pass
        else:
            assert False, 'Failed to raise KeyError'

    def test_load_multiple_times_entry_points(self):
        # We expect to get the same EntryPoint object because we save them
        # in the cache.
        em1 = extension.ExtensionManager('stevedore.test.extension')
        eps1 = [ext.entry_point for ext in em1]
        em2 = extension.ExtensionManager('stevedore.test.extension')
        eps2 = [ext.entry_point for ext in em2]
        self.assertIs(eps1[0], eps2[0])

    def test_load_multiple_times_plugins(self):
        # We expect to get the same plugin object (module or class)
        # because the underlying import machinery will cache the values.
        em1 = extension.ExtensionManager('stevedore.test.extension')
        plugins1 = [ext.plugin for ext in em1]
        em2 = extension.ExtensionManager('stevedore.test.extension')
        plugins2 = [ext.plugin for ext in em2]
        self.assertIs(plugins1[0], plugins2[0])

    def test_use_cache(self):
        # If we insert something into the cache of entry points,
        # the manager should not have to call into pkg_resources
        # to find the plugins.
        cache = extension.ExtensionManager.ENTRY_POINT_CACHE
        cache['stevedore.test.faux'] = []
        with mock.patch('pkg_resources.iter_entry_points',
                        side_effect=
                        AssertionError('called iter_entry_points')):
            em = extension.ExtensionManager('stevedore.test.faux')
            names = em.names()
        self.assertEqual(names, [])

    def test_iterable(self):
        em = extension.ExtensionManager('stevedore.test.extension')
        names = sorted(e.name for e in em)
        self.assertEqual(names, ALL_NAMES)

    def test_invoke_on_load(self):
        em = extension.ExtensionManager('stevedore.test.extension',
                                        invoke_on_load=True,
                                        invoke_args=('a',),
                                        invoke_kwds={'b': 'B'},
                                        )
        self.assertEqual(len(em.extensions), 2)
        for e in em.extensions:
            self.assertEqual(e.obj.args, ('a',))
            self.assertEqual(e.obj.kwds, {'b': 'B'})

    def test_map_return_values(self):
        def mapped(ext, *args, **kwds):
            return ext.name

        em = extension.ExtensionManager('stevedore.test.extension',
                                        invoke_on_load=True,
                                        )
        results = em.map(mapped)
        self.assertEqual(sorted(results), WORKING_NAMES)

    def test_map_arguments(self):
        objs = []

        def mapped(ext, *args, **kwds):
            objs.append((ext, args, kwds))

        em = extension.ExtensionManager('stevedore.test.extension',
                                        invoke_on_load=True,
                                        )
        em.map(mapped, 1, 2, a='A', b='B')
        self.assertEqual(len(objs), 2)
        names = sorted([o[0].name for o in objs])
        self.assertEqual(names, WORKING_NAMES)
        for o in objs:
            self.assertEqual(o[1], (1, 2))
            self.assertEqual(o[2], {'a': 'A', 'b': 'B'})

    def test_map_eats_errors(self):
        def mapped(ext, *args, **kwds):
            raise RuntimeError('hard coded error')

        em = extension.ExtensionManager('stevedore.test.extension',
                                        invoke_on_load=True,
                                        )
        results = em.map(mapped, 1, 2, a='A', b='B')
        self.assertEqual(results, [])

    def test_map_propagate_exceptions(self):
        def mapped(ext, *args, **kwds):
            raise RuntimeError('hard coded error')

        em = extension.ExtensionManager('stevedore.test.extension',
                                        invoke_on_load=True,
                                        propagate_map_exceptions=True
                                        )

        try:
            em.map(mapped, 1, 2, a='A', b='B')
            assert False
        except RuntimeError:
            pass

    def test_map_errors_when_no_plugins(self):
        expected_str = 'No stevedore.test.extension.none extensions found'

        def mapped(ext, *args, **kwds):
            pass

        em = extension.ExtensionManager('stevedore.test.extension.none',
                                        invoke_on_load=True,
                                        )
        try:
            em.map(mapped, 1, 2, a='A', b='B')
        except RuntimeError as err:
            self.assertEqual(expected_str, str(err))

    def test_map_method(self):
        em = extension.ExtensionManager('stevedore.test.extension',
                                        invoke_on_load=True,
                                        )

        result = em.map_method('get_args_and_data', 42)
        self.assertEqual(set(r[2] for r in result), set([42]))


class TestLoadRequirementsNewSetuptools(utils.TestCase):
    # setuptools 11.3 and later

    def setUp(self):
        super(TestLoadRequirementsNewSetuptools, self).setUp()
        self.mock_ep = mock.Mock(spec=['require', 'resolve', 'load', 'name'])
        self.em = extension.ExtensionManager.make_test_instance([])

    def test_verify_requirements(self):
        self.em._load_one_plugin(self.mock_ep, False, (), {},
                                 verify_requirements=True)
        self.mock_ep.require.assert_called_once_with()
        self.mock_ep.resolve.assert_called_once_with()

    def test_no_verify_requirements(self):
        self.em._load_one_plugin(self.mock_ep, False, (), {},
                                 verify_requirements=False)
        self.assertEqual(0, self.mock_ep.require.call_count)
        self.mock_ep.resolve.assert_called_once_with()


class TestLoadRequirementsOldSetuptools(utils.TestCase):
    # Before setuptools 11.3

    def setUp(self):
        super(TestLoadRequirementsOldSetuptools, self).setUp()
        self.mock_ep = mock.Mock(spec=['load', 'name'])
        self.em = extension.ExtensionManager.make_test_instance([])

    def test_verify_requirements(self):
        self.em._load_one_plugin(self.mock_ep, False, (), {},
                                 verify_requirements=True)
        self.mock_ep.load.assert_called_once_with(require=True)

    def test_no_verify_requirements(self):
        self.em._load_one_plugin(self.mock_ep, False, (), {},
                                 verify_requirements=False)
        self.mock_ep.load.assert_called_once_with(require=False)
