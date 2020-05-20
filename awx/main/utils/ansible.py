# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import codecs
import re
import os
import logging
from itertools import islice
from configparser import ConfigParser

# Django
from django.utils.encoding import smart_str

logger = logging.getLogger('awx.main.utils.ansible')


__all__ = ['skip_directory', 'could_be_playbook', 'could_be_inventory']


valid_playbook_re = re.compile(r'^\s*?-?\s*?(?:hosts|include|import_playbook):\s*?.*?$')
valid_inventory_re = re.compile(r'^[a-zA-Z0-9_.=\[\]]')


def skip_directory(relative_directory_path):
    path_elements = relative_directory_path.split(os.sep)
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
    # Exclude anything inside of group or host vars directories
    if 'group_vars' in path_elements or 'host_vars' in path_elements:
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
        for n, line in enumerate(codecs.open(
            playbook_path,
            'r',
            encoding='utf-8',
            errors='ignore'
        )):
            if valid_playbook_re.match(line):
                matched = True
                break
            # Any YAML file can also be encrypted with vault;
            # allow these to be used as the main playbook.
            elif n == 0 and line.startswith('$ANSIBLE_VAULT;'):
                matched = True
                break
    except IOError:
        return None
    if not matched:
        return None
    return os.path.relpath(playbook_path, smart_str(project_path))


def could_be_inventory(project_path, dir_path, filename):
    # Decisions based exclusively on filename
    inventory_path = os.path.join(dir_path, filename)
    inventory_rel_path = os.path.relpath(inventory_path, smart_str(project_path))
    suspected_ext = os.path.splitext(filename)[-1]
    if filename in ['inventory', 'hosts']:
        # Users commonly name their inventory files these names
        return inventory_rel_path
    elif suspected_ext == '.ini' or os.access(inventory_path, os.X_OK):
        # Files with any of these extensions are always included
        return inventory_rel_path
    elif '.' in suspected_ext:
        # If not using those extensions, inventory must have _no_ extension
        return None

    # Filter files that do not use a character set consistent with
    # Ansible inventory mainly
    try:
        # only read through first 10 lines for performance
        with codecs.open(
            inventory_path,
            'r',
            encoding='utf-8',
            errors='ignore'
        ) as inv_file:
            for line in islice(inv_file, 10):
                if not valid_inventory_re.match(line):
                    return None
    except IOError:
        return None
    return inventory_rel_path


def read_ansible_config(project_path, variables_of_interest):
    fnames = ['/etc/ansible/ansible.cfg']
    if project_path:
        fnames.append(os.path.join(project_path, 'ansible.cfg'))
    values = {}
    try:
        parser = ConfigParser()
        parser.read(fnames)
        if 'defaults' in parser:
            for var in variables_of_interest:
                if var in parser['defaults']:
                    values[var] = parser['defaults'][var]
    except Exception:
        logger.exception('Failed to read ansible configuration(s) {}'.format(fnames))
    return values
