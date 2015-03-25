#!/usr/bin/env python

import os
import stat
from ansible.module_utils.basic import * # noqa

def main():
    module = AnsibleModule(
        argument_spec = dict(path=dict(required=True),
                             get_checksum=dict(required=False, default='no', type='bool')))
    files = []
    path = module.params.get('path')
    path = os.path.expanduser(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        module.fail_json(msg = "Given path must exist and be a directory")

    get_checksum = module.params.get('get_checksum')
    for filepath in [os.path.join(w_path, f) for w_path, w_names, w_file in os.walk(path) for f in w_file]:
        try:
            st = os.stat(filepath)
        except OSError, e:
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
