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

def transform_users_set_to_objects(users_info_set):
    users = []
    for user_info in users_info_set:
        user_array = user_info.split(';')
        user = {
            'username': user_array[0],
            'first_name': user_array[1],
            'last_name': user_array[2],
            'email': user_array[3]
        }
        users.append(user)
    return users
