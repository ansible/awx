from __future__ import absolute_import, division, print_function

__metaclass__ = type

import errno
import os
import tarfile
import zipfile

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

try:
    from zipfile import BadZipFile
except ImportError:
    from zipfile import BadZipfile as BadZipFile  # py2 compat


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False

        result = super(ActionModule, self).run(tmp, task_vars)

        src = self._task.args.get("src")
        proj_path = self._task.args.get("project_path")
        force = self._task.args.get("force", False)

        try:
            archive = zipfile.ZipFile(src)
            get_filenames = archive.namelist
            get_members = archive.infolist
        except BadZipFile:
            try:
                archive = tarfile.open(src)
            except tarfile.ReadError:
                result["failed"] = True
                result["msg"] = "{0} is not a valid archive".format(src)
                return result
            get_filenames = archive.getnames
            get_members = archive.getmembers

        # Most well formed archives contain a single root directory, typically named
        # project-name-1.0.0. The project contents should be inside that directory.
        start_index = 0
        root_contents = set(
            [filename.split(os.path.sep)[0] for filename in get_filenames()]
        )
        if len(root_contents) == 1:
            start_index = len(list(root_contents)[0]) + 1

        for member in get_members():
            try:
                filename = member.filename
            except AttributeError:
                filename = member.name

            # Skip the archive base directory
            if not filename[start_index:]:
                continue

            dest = os.path.join(proj_path, filename[start_index:])

            if not force and os.path.exists(dest):
                continue

            try:
                is_dir = member.is_dir()
            except AttributeError:
                try:
                    is_dir = member.isdir()
                except AttributeError:
                    is_dir = member.filename[-1] == '/'  # py2 compat for ZipInfo

            if is_dir:
                try:
                    os.makedirs(dest)
                except OSError as exc:  # Python >= 2.5
                    if exc.errno == errno.EEXIST and os.path.isdir(dest):
                        pass
                    else:
                        raise
            else:
                try:
                    member_f = archive.open(member)
                except TypeError:
                    member_f = tarfile.ExFileObject(archive, member)

                with open(dest, "wb") as f:
                    f.write(member_f.read())
                    member_f.close()

        archive.close()

        result["changed"] = True
        return result
