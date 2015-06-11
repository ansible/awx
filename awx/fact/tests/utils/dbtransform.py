# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# AWX
from awx.main.tests.base import BaseTest
from awx.fact.models.fact import * # noqa
from awx.fact.utils.dbtransform import KeyTransform

#__all__ = ['DBTransformTest', 'KeyTransformUnitTest']
__all__ = ['KeyTransformUnitTest']

class KeyTransformUnitTest(BaseTest):
    def setUp(self):
        super(KeyTransformUnitTest, self).setUp()
        self.key_transform = KeyTransform([('.', '\uff0E'), ('$', '\uff04')])

    def test_no_replace(self):
        value = {
            "a_key_with_a_dict" : {
                "key" : "value",
                "nested_key_with_dict": {
                    "nested_key_with_value" : "deep_value"
                }
            }
        }

        data = self.key_transform.transform_incoming(value, None)
        self.assertEqual(data, value)

        data = self.key_transform.transform_outgoing(value, None)
        self.assertEqual(data, value)

    def test_complex(self):
        value = {
            "a.key.with.a.dict" : {
                "key" : "value",
                "nested.key.with.dict": {
                    "nested.key.with.value" : "deep_value"
                }
            }
        }
        value_transformed = {
            "a\uff0Ekey\uff0Ewith\uff0Ea\uff0Edict" : {
                "key" : "value",
                "nested\uff0Ekey\uff0Ewith\uff0Edict": {
                    "nested\uff0Ekey\uff0Ewith\uff0Evalue" : "deep_value"
                }
            }
        }

        data = self.key_transform.transform_incoming(value, None)
        self.assertEqual(data, value_transformed)

        data = self.key_transform.transform_outgoing(value_transformed, None)
        self.assertEqual(data, value)

    def test_simple(self):
        value = {
            "a.key" : "value"
        }
        value_transformed = {
            "a\uff0Ekey" : "value"
        }

        data = self.key_transform.transform_incoming(value, None)
        self.assertEqual(data, value_transformed)

        data = self.key_transform.transform_outgoing(value_transformed, None)
        self.assertEqual(data, value)

    def test_nested_dict(self):
        value = {
            "a.key.with.a.dict" : {
                "nested.key." : "value"
            }
        }
        value_transformed = {
            "a\uff0Ekey\uff0Ewith\uff0Ea\uff0Edict" : {
                "nested\uff0Ekey\uff0E" : "value"
            }
        }

        data = self.key_transform.transform_incoming(value, None)
        self.assertEqual(data, value_transformed)
        
        data = self.key_transform.transform_outgoing(value_transformed, None)
        self.assertEqual(data, value)

    def test_array(self):
        value = {
            "a.key.with.an.array" : [
                {
                    "key.with.dot" : "value"
                }
            ]
        }
        value_transformed = {
            "a\uff0Ekey\uff0Ewith\uff0Ean\uff0Earray" : [
                {
                    "key\uff0Ewith\uff0Edot" : "value"
                }
            ]
        }
        data = self.key_transform.transform_incoming(value, None)
        self.assertEqual(data, value_transformed)
        
        data = self.key_transform.transform_outgoing(value_transformed, None)
        self.assertEqual(data, value)

'''
class DBTransformTest(BaseTest, MongoDBRequired):
'''
