from stevedore import hook
from stevedore.tests import utils


class TestHook(utils.TestCase):
    def test_hook(self):
        em = hook.HookManager(
            'stevedore.test.extension',
            't1',
            invoke_on_load=True,
            invoke_args=('a',),
            invoke_kwds={'b': 'B'},
        )
        self.assertEqual(len(em.extensions), 1)
        self.assertEqual(em.names(), ['t1'])

    def test_get_by_name(self):
        em = hook.HookManager(
            'stevedore.test.extension',
            't1',
            invoke_on_load=True,
            invoke_args=('a',),
            invoke_kwds={'b': 'B'},
        )
        e_list = em['t1']
        self.assertEqual(len(e_list), 1)
        e = e_list[0]
        self.assertEqual(e.name, 't1')

    def test_get_by_name_missing(self):
        em = hook.HookManager(
            'stevedore.test.extension',
            't1',
            invoke_on_load=True,
            invoke_args=('a',),
            invoke_kwds={'b': 'B'},
        )
        try:
            em['t2']
        except KeyError:
            pass
        else:
            assert False, 'Failed to raise KeyError'
