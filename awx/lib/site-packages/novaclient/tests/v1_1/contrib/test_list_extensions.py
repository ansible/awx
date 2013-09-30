from novaclient import extension
from novaclient.v1_1.contrib import list_extensions

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


extensions = [
    extension.Extension(list_extensions.__name__.split(".")[-1],
                        list_extensions),
]
cs = fakes.FakeClient(extensions=extensions)


class ListExtensionsTests(utils.TestCase):
    def test_list_extensions(self):
        all_exts = cs.list_extensions.show_all()
        cs.assert_called('GET', '/extensions')
        self.assertTrue(len(all_exts) > 0)
        for r in all_exts:
            self.assertTrue(len(r.summary) > 0)
