# Copyright (c) 2014, Ansible, Inc.
# All Rights Reserved.

# Pymongo
from pymongo.son_manipulator import SONManipulator

class KeyTransform(SONManipulator):

    def __init__(self, replace):
        self.replace = replace

    def replace_key(self, key):
        for (replace, replacement) in self.replace:
                key = key.replace(replace, replacement)
        return key

    def revert_key(self, key):
        for (replacement, replace) in self.replace:
                key = key.replace(replace, replacement)
        return key

    def replace_incoming(self, obj):
        if isinstance(obj, dict):
            value = {}
            for k, v in obj.items():
                value[self.replace_key(k)] = self.replace_incoming(v)
        elif isinstance(obj, list):
            value = [self.replace_incoming(elem)
                     for elem in obj]
        else:
            value = obj

        return value

    def replace_outgoing(self, obj):
        if isinstance(obj, dict):
            value = {}
            for k, v in obj.items():
                value[self.revert_key(k)] = self.replace_outgoing(v)
        elif isinstance(obj, list):
            value = [self.replace_outgoing(elem)
                     for elem in obj]
        else:
            value = obj

        return value

    def transform_incoming(self, son, collection):
        return self.replace_incoming(son)

    def transform_outgoing(self, son, collection):
        return self.replace_outgoing(son)

def register_key_transform(db):
    db.add_son_manipulator(KeyTransform([('.', '\uff0E'), ('$', '\uff04')]))
