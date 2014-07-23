import sys
import unittest

from libcloud.loadbalancer.types import Provider
from libcloud.loadbalancer.providers import get_driver


class NinefoldLbTestCase(unittest.TestCase):
    def test_driver_instantiation(self):
        cls = get_driver(Provider.NINEFOLD)
        cls('username', 'key')


if __name__ == '__main__':
    sys.exit(unittest.main())
