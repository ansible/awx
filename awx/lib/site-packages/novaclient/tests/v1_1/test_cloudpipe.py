from novaclient.v1_1 import cloudpipe
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class CloudpipeTest(utils.TestCase):

    def test_list_cloudpipes(self):
        cp = cs.cloudpipe.list()
        cs.assert_called('GET', '/os-cloudpipe')
        [self.assertTrue(isinstance(c, cloudpipe.Cloudpipe)) for c in cp]

    def test_create(self):
        project = "test"
        cp = cs.cloudpipe.create(project)
        body = {'cloudpipe': {'project_id': project}}
        cs.assert_called('POST', '/os-cloudpipe', body)
        self.assertTrue(isinstance(cp, str))

    def test_update(self):
        cs.cloudpipe.update("192.168.1.1", 2345)
        body = {'configure_project': {'vpn_ip': "192.168.1.1",
                                      'vpn_port': 2345}}
        cs.assert_called('PUT', '/os-cloudpipe/configure-project', body)
