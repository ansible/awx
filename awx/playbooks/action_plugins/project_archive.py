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


class UnsafeArchivePathError(Exception):
    pass


class UnsupportedArchiveError(Exception):
    pass


def resolve_archive_member_path(proj_path: str, filename: str, start_index: int) -> str:
    """Resolve the on-disk destination for an archive member.

    Rejects members whose name would extract outside of proj_path via an
    absolute path or '..' traversal component.
    """
    relative_name = filename[start_index:]

    if os.path.isabs(relative_name):
        raise UnsafeArchivePathError("Archive member '{0}' has an absolute path and is not allowed".format(filename))

    proj_real = os.path.realpath(proj_path)
    dest = os.path.realpath(os.path.join(proj_real, relative_name))
    root_prefix = proj_real + os.sep
    if not (dest.startswith(root_prefix) or dest == proj_real):
        raise UnsafeArchivePathError("Archive member '{0}' would extract outside of the project path".format(filename))

    return dest


def open_project_archive(src):
    """Open src as a zip or tar archive, returning (archive, get_filenames, get_members) accessors."""
    try:
        archive = zipfile.ZipFile(src)
        return archive, archive.namelist, archive.infolist
    except BadZipFile:
        pass

    try:
        archive = tarfile.open(src)
    except tarfile.ReadError:
        raise UnsupportedArchiveError("{0} is not a valid archive".format(src))

    return archive, archive.getnames, archive.getmembers


def compute_start_index(filenames):
    """Most well formed archives contain a single root directory, typically named
    project-name-1.0.0. The project contents should be inside that directory."""
    root_contents = set(filename.split(os.path.sep)[0] for filename in filenames)
    if len(root_contents) != 1:
        return 0
    return len(next(iter(root_contents))) + 1


def get_member_filename(member):
    try:
        return member.filename
    except AttributeError:
        return member.name


def member_is_dir(member):
    try:
        return member.is_dir()
    except AttributeError:
        pass

    try:
        return member.isdir()
    except AttributeError:
        return member.filename[-1] == '/'  # py2 compat for ZipInfo


def make_member_dir(dest):
    try:
        os.makedirs(dest)
    except OSError as exc:  # Python >= 2.5
        if exc.errno != errno.EEXIST or not os.path.isdir(dest):
            raise


def write_member_file(archive, member, dest):
    try:
        member_f = archive.open(member)
    except TypeError:
        member_f = tarfile.ExFileObject(archive, member)

    with open(dest, "wb") as f:
        f.write(member_f.read())
        member_f.close()


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False

        result = super(ActionModule, self).run(tmp, task_vars)

        src = self._task.args.get("src")
        proj_path = self._task.args.get("project_path")
        force = self._task.args.get("force", False)

        try:
            archive, get_filenames, get_members = open_project_archive(src)
        except UnsupportedArchiveError as exc:
            result["failed"] = True
            result["msg"] = str(exc)
            return result

        start_index = compute_start_index(get_filenames())

        for member in get_members():
            filename = get_member_filename(member)

            # Skip the archive base directory
            if not filename[start_index:]:
                continue

            try:
                dest = resolve_archive_member_path(proj_path, filename, start_index)
            except UnsafeArchivePathError as exc:
                archive.close()
                result["failed"] = True
                result["msg"] = str(exc)
                return result

            if not force and os.path.exists(dest):
                continue

            if member_is_dir(member):
                make_member_dir(dest)
            else:
                write_member_file(archive, member, dest)

        archive.close()

        result["changed"] = True
        return result
