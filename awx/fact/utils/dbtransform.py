# Copyright (c) 2014, Ansible, Inc.
# All Rights Reserved.
from pymongo.son_manipulator import SONManipulator

'''
Inspired by: https://stackoverflow.com/questions/8429318/how-to-use-dot-in-field-name/20698802#20698802

Replace . and $ with unicode values
'''
class KeyTransform(SONManipulator):
    def __init__(self, replace):
        self.replace = replace

    def transform_key(self, key, replace, replacement):
        """Transform key for saving to database."""
        return key.replace(replace, replacement)

    def revert_key(self, key, replace, replacement):
        """Restore transformed key returning from database."""
        return key.replace(replacement, replace)

    def transform_incoming(self, son, collection):
        """Recursively replace all keys that need transforming."""
        for (key, value) in son.items():
            for r in self.replace:
                replace = r[0]
                replacement = r[1]
                if replace in key:
                    if isinstance(value, dict):
                        son[self.transform_key(key, replace, replacement)] = self.transform_incoming(
                            son.pop(key), collection)
                    else:
                        son[self.transform_key(key, replace, replacement)] = son.pop(key)
                elif isinstance(value, dict):  # recurse into sub-docs
                    son[key] = self.transform_incoming(value, collection)
        return son

    def transform_outgoing(self, son, collection):
        """Recursively restore all transformed keys."""
        for (key, value) in son.items():
            for r in self.replace:
                replace = r[0]
                replacement = r[1]
                if replacement in key:
                    if isinstance(value, dict):
                        son[self.revert_key(key, replace, replacement)] = self.transform_outgoing(
                            son.pop(key), collection)
                    else:
                        son[self.revert_key(key, replace, replacement)] = son.pop(key)
                elif isinstance(value, dict):  # recurse into sub-docs
                    son[key] = self.transform_outgoing(value, collection)
        return son

def register_key_transform(db):
    db.add_son_manipulator(KeyTransform([('.', '\uff0E'), ('$', '\uff04')]))
