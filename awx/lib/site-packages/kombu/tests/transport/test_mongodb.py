from __future__ import absolute_import

from kombu import Connection

from kombu.tests.case import Case, SkipTest, skip_if_not_module


class MockConnection(dict):

    def __setattr__(self, key, value):
        self[key] = value


class test_mongodb(Case):

    @skip_if_not_module('pymongo')
    def test_url_parser(self):
        from kombu.transport import mongodb
        from pymongo.errors import ConfigurationError

        raise SkipTest(
            'Test is functional: it actually connects to mongod')

        class Transport(mongodb.Transport):
            Connection = MockConnection

        url = 'mongodb://'
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client
        self.assertEquals(client.name, 'kombu_default')
        self.assertEquals(client.connection.host, '127.0.0.1')

        url = 'mongodb://localhost'
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client
        self.assertEquals(client.name, 'kombu_default')

        url = 'mongodb://localhost/dbname'
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client
        self.assertEquals(client.name, 'dbname')

        url = 'mongodb://localhost,localhost:29017/dbname'
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client

        nodes = client.connection.nodes
        # If there's just 1 node it is because we're  connecting to a single
        # server instead of a repl / mongoss.
        if len(nodes) == 2:
            self.assertTrue(('localhost', 29017) in nodes)
            self.assertEquals(client.name, 'dbname')

        # Passing options breaks kombu's _init_params method
        # url = 'mongodb://localhost,localhost2:29017/dbname?safe=true'
        # c = Connection(url, transport=Transport).connect()
        # client = c.channels[0].client

        url = 'mongodb://localhost:27017,localhost2:29017/dbname'
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client

        # Login to admin db since there's no db specified
        url = "mongodb://adminusername:adminpassword@localhost"
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client
        self.assertEquals(client.name, "kombu_default")

        # Lets make sure that using admin db doesn't break anything
        # when no user is specified
        url = "mongodb://localhost"
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client

        # Assuming there's user 'username' with password 'password'
        # configured in mongodb
        url = "mongodb://username:password@localhost/dbname"
        c = Connection(url, transport=Transport).connect()
        client = c.channels[0].client

        # Assuming there's no user 'nousername' with password 'nopassword'
        # configured in mongodb
        url = "mongodb://nousername:nopassword@localhost/dbname"
        c = Connection(url, transport=Transport).connect()

        # Needed, otherwise the error would be rose before
        # the assertRaises is called
        def get_client():
            c.channels[0].client
        self.assertRaises(ConfigurationError, get_client)
