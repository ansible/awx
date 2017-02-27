#!/usr/bin/env python

# Python
import difflib
import glob
import os
import shutil

# RedBaron
from redbaron import RedBaron, indent

__all__ = ['comment_assignments']


def comment_assignments(patterns, assignment_names, dry_run=True, backup_suffix='.old'):
    if isinstance(patterns, basestring):
        patterns = [patterns]
    diffs = []
    for pattern in patterns:
        for filename in sorted(glob.glob(pattern)):
            filename = os.path.abspath(os.path.normpath(filename))
            if backup_suffix:
                backup_filename = '{}{}'.format(filename, backup_suffix)
            else:
                backup_filename = None
            diff = comment_assignments_in_file(filename, assignment_names, dry_run, backup_filename)
            if diff:
                diffs.append(diff)
    return diffs


def comment_assignments_in_file(filename, assignment_names, dry_run=True, backup_filename=None):
    if isinstance(assignment_names, basestring):
        assignment_names = [assignment_names]
    else:
        assignment_names = assignment_names[:]
    current_file_data = open(filename).read()

    for assignment_name in assignment_names[:]:
        if assignment_name in current_file_data:
            continue
        if assignment_name in assignment_names:
            assignment_names.remove(assignment_name)
    if not assignment_names:
        return ''

    replace_lines = {}
    rb = RedBaron(current_file_data)
    for assignment_node in rb.find_all('assignment'):
        for assignment_name in assignment_names:

            # Only target direct assignments to a variable.
            name_node = assignment_node.find('name', value=assignment_name)
            if not name_node:
                continue
            if assignment_node.target.type != 'name':
                continue

            # Build a new node that comments out the existing assignment node.
            indentation = '{}# '.format(assignment_node.indentation or '')
            new_node_content = indent(assignment_node.dumps(), indentation)
            new_node_lines = new_node_content.splitlines()
            # Add a pass statement in case the assignment block is the only
            # child in a parent code block to prevent a syntax error.
            if assignment_node.indentation:
                new_node_lines[0] = new_node_lines[0].replace(indentation, '{}pass  # '.format(assignment_node.indentation or ''), 1)
            new_node_lines[0] = '{0}This setting is now configured via the Tower API.\n{1}'.format(indentation, new_node_lines[0])

            # Store new node lines in dictionary to be replaced in file.
            start_lineno = assignment_node.absolute_bounding_box.top_left.line
            end_lineno = assignment_node.absolute_bounding_box.bottom_right.line
            for n, new_node_line in enumerate(new_node_lines):
                new_lineno = start_lineno + n
                assert new_lineno <= end_lineno
                replace_lines[new_lineno] = new_node_line

    if not replace_lines:
        return ''

    # Iterate through all lines in current file and replace as needed.
    current_file_lines = current_file_data.splitlines()
    new_file_lines = []
    for n, line in enumerate(current_file_lines):
        new_file_lines.append(replace_lines.get(n + 1, line))
    new_file_data = '\n'.join(new_file_lines)
    new_file_lines = new_file_data.splitlines()

    # If changed, syntax check and write the new file; return a diff of changes.
    diff_lines = []
    if new_file_data != current_file_data:
        compile(new_file_data, filename, 'exec')
        if backup_filename:
            from_file = backup_filename
        else:
            from_file = '{}.old'.format(filename)
        to_file = filename
        diff_lines = list(difflib.unified_diff(current_file_lines, new_file_lines, fromfile=from_file, tofile=to_file, lineterm=''))
        if not dry_run:
            if backup_filename:
                shutil.copy2(filename, backup_filename)
            with open(filename, 'wb') as fileobj:
                fileobj.write(new_file_data)
    return '\n'.join(diff_lines)


if __name__ == '__main__':
    pattern = os.path.join(os.path.dirname(__file__), '..', 'settings', 'local_*.py')
    diffs = comment_assignments(pattern, ['AUTH_LDAP_ORGANIZATION_MAP'])
    for diff in diffs:
        print(diff)
