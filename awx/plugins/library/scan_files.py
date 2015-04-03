#!/usr/bin/env python

import os
import stat
from ansible.module_utils.basic import * # noqa

DOCUMENTATION = '''
---
module: scan_files
short_description: Return file state information as fact data for a directory tree
description:
     - Return file state information recursively for a directory tree on the filesystem
version_added: "1.9"
options:
  path:
    description: The path containing files to be analyzed
    required: true
    default: null
  recursive:
    description: scan this directory and all subdirectories
    required: false
    default: no
  get_checksum:
    description: Checksum files that you can access
    required: false
    default: false
requirements: [ ]
author: Matthew Jones
'''

EXAMPLES = '''
# Example fact output:
# host | success >> {
#     "ansible_facts": {
#         "files": [
#             {
#                 "atime": 1427313854.0755742,
#                 "checksum": "cf7566e6149ad9af91e7589e0ea096a08de9c1e5",
#                 "ctime": 1427129299.22948,
#                 "dev": 51713,
#                 "gid": 0,
#                 "inode": 149601,
#                 "isblk": false,
#                 "ischr": false,
#                 "isdir": false,
#                 "isfifo": false,
#                 "isgid": false,
#                 "islnk": false,
#                 "isreg": true,
#                 "issock": false,
#                 "isuid": false,
#                 "mode": "0644",
#                 "mtime": 1427112663.0321455,
#                 "nlink": 1,
#                 "path": "/var/log/dmesg.1.gz",
#                 "rgrp": true,
#                 "roth": true,
#                 "rusr": true,
#                 "size": 28,
#                 "uid": 0,
#                 "wgrp": false,
#                 "woth": false,
#                 "wusr": true,
#                 "xgrp": false,
#                 "xoth": false,
#                 "xusr": false
#             },
#             {
#                 "atime": 1427314385.1155744,
#                 "checksum": "16fac7be61a6e4591a33ef4b729c5c3302307523",
#                 "ctime": 1427384148.5755742,
#                 "dev": 51713,
#                 "gid": 43,
#                 "inode": 149564,
#                 "isblk": false,
#                 "ischr": false,
#                 "isdir": false,
#                 "isfifo": false,
#                 "isgid": false,
#                 "islnk": false,
#                 "isreg": true,
#                 "issock": false,
#                 "isuid": false,
#                 "mode": "0664",
#                 "mtime": 1427384148.5755742,
#                 "nlink": 1,
#                 "path": "/var/log/wtmp",
#                 "rgrp": true,
#                 "roth": true,
#                 "rusr": true,
#                 "size": 48768,
#                 "uid": 0,
#                 "wgrp": true,
#                 "woth": false,
#                 "wusr": true,
#                 "xgrp": false,
#                 "xoth": false,
#                 "xusr": false
#             },
'''

def main():
    module = AnsibleModule(
        argument_spec = dict(path=dict(required=True),
                             recursive=dict(required=False, default='no', type='bool'),
                             get_checksum=dict(required=False, default='no', type='bool')))
    files = []
    path = module.params.get('path')
    path = os.path.expanduser(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        module.fail_json(msg = "Given path must exist and be a directory")

    get_checksum = module.params.get('get_checksum')
    should_recurse = module.params.get('recursive')
    if not should_recurse:
        path_list = [os.path.join(path, subpath) for subpath in os.listdir(path)]
    else:
        path_list = [os.path.join(w_path, f) for w_path, w_names, w_file in os.walk(path) for f in w_file]
    for filepath in path_list:
        try:
            st = os.stat(filepath)
        except OSError:
            continue

        mode = st.st_mode
        d = {
            'path'     : filepath,
            'mode'     : "%04o" % stat.S_IMODE(mode),
            'isdir'    : stat.S_ISDIR(mode),
            'ischr'    : stat.S_ISCHR(mode),
            'isblk'    : stat.S_ISBLK(mode),
            'isreg'    : stat.S_ISREG(mode),
            'isfifo'   : stat.S_ISFIFO(mode),
            'islnk'    : stat.S_ISLNK(mode),
            'issock'   : stat.S_ISSOCK(mode),
            'uid'      : st.st_uid,
            'gid'      : st.st_gid,
            'size'     : st.st_size,
            'inode'    : st.st_ino,
            'dev'      : st.st_dev,
            'nlink'    : st.st_nlink,
            'atime'    : st.st_atime,
            'mtime'    : st.st_mtime,
            'ctime'    : st.st_ctime,
            'wusr'     : bool(mode & stat.S_IWUSR),
            'rusr'     : bool(mode & stat.S_IRUSR),
            'xusr'     : bool(mode & stat.S_IXUSR),
            'wgrp'     : bool(mode & stat.S_IWGRP),
            'rgrp'     : bool(mode & stat.S_IRGRP),
            'xgrp'     : bool(mode & stat.S_IXGRP),
            'woth'     : bool(mode & stat.S_IWOTH),
            'roth'     : bool(mode & stat.S_IROTH),
            'xoth'     : bool(mode & stat.S_IXOTH),
            'isuid'    : bool(mode & stat.S_ISUID),
            'isgid'    : bool(mode & stat.S_ISGID),
        }
        if get_checksum and stat.S_ISREG(mode) and os.access(filepath, os.R_OK):
            d['checksum'] = module.sha1(filepath)
        files.append(d)
    results = dict(ansible_facts=dict(files=files))
    module.exit_json(**results)

main()
