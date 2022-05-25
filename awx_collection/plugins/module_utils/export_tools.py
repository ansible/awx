#!/usr/bin/python
import json
import yaml

def parse_extra_vars_to_json(extra_vars):
    if isinstance(extra_vars, str):
        extra_vars = json.dump(yaml.safe_load(extra_vars))
        if extra_vars == 'null':
            return dict()
    return extra_vars

def is_object_in_list_by_id(object_id, list):
    for object in list:
        if object['id'] == object_id:
            return True
    return False
