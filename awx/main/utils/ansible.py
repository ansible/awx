# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import re
import os
from itertools import islice

# Django
from django.utils.encoding import smart_str


__all__ = ['could_be_playbook', 'could_be_inventory']


valid_playbook_re = re.compile(r'^\s*?-?\s*?(?:hosts|include):\s*?.*?$')
valid_inventory_re = re.compile(r'^[a-zA-Z0-9_.=\[\]]')


def _skip_directory(rel_path):
    path_elements = rel_path.split(os.sep)
    # Exclude files in a roles subdirectory.
    if 'roles' in path_elements:
        return True
    # Filter files in a tasks subdirectory.
    if 'tasks' in path_elements:
        return True
    for element in path_elements:
        # Do not include dot files or dirs
        if element.startswith('.'):
            return True
    return False


def could_be_playbook(project_path, dir_path, filename):
    if os.path.splitext(filename)[-1] not in ['.yml', '.yaml']:
        return None
    playbook_path = os.path.join(dir_path, filename)
    # Filter files that do not have either hosts or top-level
    # includes. Use regex to allow files with invalid YAML to
    # show up.
    matched = False
    try:
        for n, line in enumerate(file(playbook_path)):
            if valid_playbook_re.match(line):
                matched = True
            # Any YAML file can also be encrypted with vault;
            # allow these to be used as the main playbook.
            elif n == 0 and line.startswith('$ANSIBLE_VAULT;'):
                matched = True
    except IOError:
        return None
    if not matched:
        return None
    playbook = os.path.relpath(playbook_path, smart_str(project_path))
    if _skip_directory(playbook):
        return None
    return playbook


def could_be_inventory(project_path, dir_path, filename):
    suspected_ext = os.path.splitext(filename)[-1]
    # Allow for files with no extension, or with extensions in a certain set
    if '.' in suspected_ext and suspected_ext not in ['.yml', '.yaml', '.ini']:
        return None
    inventory_path = os.path.join(dir_path, filename)
    # Filter files that do not use a character set consistent with
    # Ansible inventory mainly
    try:
        # only read through first 10 lines for performance
        with open(inventory_path) as inv_file:
            for line in islice(inv_file, 10):
                if not valid_inventory_re.match(line):
                    return None
    except IOError:
        return None
    inventory = os.path.relpath(inventory_path, smart_str(project_path))
    if _skip_directory(inventory):
        return None
    return inventory
