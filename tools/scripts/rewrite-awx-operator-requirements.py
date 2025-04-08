#!/usr/bin/env python3

import yaml
import sys


AWX_ENTRY = 'https://github.com/ansible/awx.git#/awx_collection/'


def load_yaml_file(fname):
    with open(fname, 'r') as file:
        data = yaml.safe_load(file)
    return data


def write_yaml_file(fname, data):
    with open(fname, 'w') as file:
        yaml.dump(data, file)


def replace_awx(data, path):
    for entry in data['collections']:
        if entry['name'] == AWX_ENTRY or entry['name'] == 'awx.awx':
            entry['name'] = f'file://{path}#/awx_collection/'
            entry['type'] = 'git'
            entry.pop('version', None)
            return data

    raise ValueError(f"Failed to find {AWX_ENTRY} in {data}")


def run(fname, awx_path):
    write_yaml_file(fname, replace_awx(load_yaml_file(fname), awx_path))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        run(sys.argv[1], sys.argv[2])
    else:
        print(f"Usage: {sys.argv[0]} <awx-operator-molecule-requirements.yml> <awx-git-path>", file=sys.stderr)
