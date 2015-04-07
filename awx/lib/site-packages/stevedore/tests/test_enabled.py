from stevedore import enabled
from stevedore.tests import utils


class TestEnabled(utils.TestCase):
    def test_enabled(self):
        def check_enabled(ep):
            return ep.name == 't2'
        em = enabled.EnabledExtensionManager(
            'stevedore.test.extension',
            check_enabled,
            invoke_on_load=True,
            invoke_args=('a',),
            invoke_kwds={'b': 'B'},
        )
        self.assertEqual(len(em.extensions), 1)
        self.assertEqual(em.names(), ['t2'])

    def test_enabled_after_load(self):
        def check_enabled(ext):
            return ext.obj and ext.name == 't2'
        em = enabled.EnabledExtensionManager(
            'stevedore.test.extension',
            check_enabled,
            invoke_on_load=True,
            invoke_args=('a',),
            invoke_kwds={'b': 'B'},
        )
        self.assertEqual(len(em.extensions), 1)
        self.assertEqual(em.names(), ['t2'])
