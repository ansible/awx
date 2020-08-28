from __future__ import absolute_import, division, print_function

__metaclass__ = type

import zipfile
import tarfile
import os

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


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
        except zipfile.BadZipFile:
            archive = tarfile.open(src)
            get_filenames = archive.getnames
            get_members = archive.getmembers
        except tarfile.ReadError:
            result["failed"] = True
            result["msg"] = "{0} is not a valid archive".format(src)
            return result

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
                is_dir = member.isdir()

            if is_dir:
                os.makedirs(dest, exist_ok=True)
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
