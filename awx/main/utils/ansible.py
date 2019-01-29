# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import codecs
import re
import os
from itertools import islice

# Django
from django.utils.encoding import smart_str


__all__ = ['skip_directory', 'could_be_playbook', 'could_be_inventory', 'filter_non_json_lines']


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


# This method is copied directly from Ansible core code base
# lib/ansible/module_utils/json_utils.py
# For purpose, see: https://github.com/ansible/ansible/issues/50100
# Any patches to this method should sync from that version
# NB: a copy of this function exists in ../../modules/core/async_wrapper.py. Ensure any
# changes are propagated there.
def _filter_non_json_lines(data):
    '''
    Used to filter unrelated output around module JSON output, like messages from
    tcagetattr, or where dropbear spews MOTD on every single command (which is nuts).
    Filters leading lines before first line-starting occurrence of '{' or '[', and filter all
    trailing lines after matching close character (working from the bottom of output).
    '''
    warnings = []

    # Filter initial junk
    lines = data.splitlines()

    for start, line in enumerate(lines):
        line = line.strip()
        if line.startswith(u'{'):
            endchar = u'}'
            break
        elif line.startswith(u'['):
            endchar = u']'
            break
    else:
        raise ValueError('No start of json char found')

    # Filter trailing junk
    lines = lines[start:]

    for reverse_end_offset, line in enumerate(reversed(lines)):
        if line.strip().endswith(endchar):
            break
    else:
        raise ValueError('No end of json char found')

    if reverse_end_offset > 0:
        # Trailing junk is uncommon and can point to things the user might
        # want to change.  So print a warning if we find any
        trailing_junk = lines[len(lines) - reverse_end_offset:]
        for line in trailing_junk:
            if line.strip():
                warnings.append('Module invocation had junk after the JSON data: %s' % '\n'.join(trailing_junk))
                break

    lines = lines[:(len(lines) - reverse_end_offset)]

    # NOTE: warnings are undesired (would prevent JSON parsing)
    # so this change diverges from the source by not using the warnings
    # original:
    # return ('\n'.join(lines), warnings)
    return '\n'.join(lines)


def filter_non_json_lines(data):
    # Optimization on top of Ansible's method to avoid operations on large
    # strings when it is given in standard ansible-inventory form
    if data.startswith(u'{') and data.endswith(u'}'):
        return data
    return _filter_non_json_lines(data)
