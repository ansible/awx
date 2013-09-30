from novaclient.v1_1 import images
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class ImagesTest(utils.TestCase):

    def test_list_images(self):
        il = cs.images.list()
        cs.assert_called('GET', '/images/detail')
        [self.assertTrue(isinstance(i, images.Image)) for i in il]

    def test_list_images_undetailed(self):
        il = cs.images.list(detailed=False)
        cs.assert_called('GET', '/images')
        [self.assertTrue(isinstance(i, images.Image)) for i in il]

    def test_list_images_with_limit(self):
        il = cs.images.list(limit=4)
        cs.assert_called('GET', '/images/detail?limit=4')

    def test_get_image_details(self):
        i = cs.images.get(1)
        cs.assert_called('GET', '/images/1')
        self.assertTrue(isinstance(i, images.Image))
        self.assertEqual(i.id, 1)
        self.assertEqual(i.name, 'CentOS 5.2')

    def test_delete_image(self):
        cs.images.delete(1)
        cs.assert_called('DELETE', '/images/1')

    def test_delete_meta(self):
        cs.images.delete_meta(1, {'test_key': 'test_value'})
        cs.assert_called('DELETE', '/images/1/metadata/test_key')

    def test_set_meta(self):
        cs.images.set_meta(1, {'test_key': 'test_value'})
        cs.assert_called('POST', '/images/1/metadata',
                         {"metadata": {'test_key': 'test_value'}})

    def test_find(self):
        i = cs.images.find(name="CentOS 5.2")
        self.assertEqual(i.id, 1)
        cs.assert_called('GET', '/images', pos=-2)
        cs.assert_called('GET', '/images/1', pos=-1)

        iml = cs.images.findall(status='SAVING')
        self.assertEqual(len(iml), 1)
        self.assertEqual(iml[0].name, 'My Server Backup')
