"""
Unit tests for the project_archive action plugin's archive extraction path safety.
"""

import io
import os
import sys
import tarfile
import zipfile
from unittest import mock

import pytest


# project_archive.py imports from ansible.plugins.action.ActionBase and
# ansible.utils.display.Display at module load time. ansible isn't guaranteed
# importable in this test environment, so fake just enough of it for this one
# import; the mock is removed again immediately afterwards since the module,
# once imported, is cached in sys.modules and won't need it again.
class MockActionBase:
    def __init__(self, *args, **kwargs):
        self._task = mock.MagicMock()

    def run(self, tmp=None, task_vars=None):
        return {}


with mock.patch.dict(
    sys.modules,
    {
        'ansible': mock.MagicMock(),
        'ansible.plugins': mock.MagicMock(),
        'ansible.plugins.action': mock.MagicMock(ActionBase=MockActionBase),
        'ansible.utils': mock.MagicMock(),
        'ansible.utils.display': mock.MagicMock(Display=mock.MagicMock()),
    },
):
    from awx.playbooks.action_plugins.project_archive import ActionModule, UnsafeArchivePathError, resolve_archive_member_path


@pytest.fixture
def proj_path(tmp_path):
    proj = tmp_path / "project"
    proj.mkdir()
    return str(proj)


def make_action_module(src, project_path, force=False):
    action = ActionModule.__new__(ActionModule)
    action._task = mock.MagicMock()
    action._task.args = {"src": src, "project_path": project_path, "force": force}
    return action


class TestResolveArchiveMemberPath:
    def test_legitimate_nested_path(self, proj_path):
        dest = resolve_archive_member_path(proj_path, "projroot/sub/file.txt", len("projroot/"))
        assert dest == os.path.realpath(os.path.join(proj_path, "sub/file.txt"))

    def test_relative_traversal_rejected(self, proj_path):
        with pytest.raises(UnsafeArchivePathError):
            resolve_archive_member_path(proj_path, "projroot/../../../../tmp/marker.txt", len("projroot/"))

    def test_absolute_path_rejected(self, proj_path):
        with pytest.raises(UnsafeArchivePathError):
            resolve_archive_member_path(proj_path, "/etc/passwd", 0)

    def test_dotdot_that_stays_inside_is_allowed(self, proj_path):
        os.makedirs(os.path.join(proj_path, "a"))
        dest = resolve_archive_member_path(proj_path, "projroot/a/../a/file.txt", len("projroot/"))
        assert dest == os.path.realpath(os.path.join(proj_path, "a/file.txt"))


def _add_tar_dir(tf, name):
    info = tarfile.TarInfo(name=name)
    info.type = tarfile.DIRTYPE
    tf.addfile(info)


def _add_tar_file(tf, name, data=b"content"):
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tf.addfile(info, io.BytesIO(data))


def _build_zip(tmp_path, names):
    src = str(tmp_path / "project.zip")
    with zipfile.ZipFile(src, "w") as zf:
        for name in names:
            if name.endswith("/"):
                zf.writestr(zipfile.ZipInfo(name), "")
            else:
                zf.writestr(name, "content")
    return src


def _build_tar(tmp_path, names):
    src = str(tmp_path / "project.tar")
    with tarfile.open(src, "w") as tf:
        for name in names:
            if name.endswith("/"):
                _add_tar_dir(tf, name.rstrip("/"))
            else:
                _add_tar_file(tf, name)
    return src


@pytest.mark.parametrize("build_archive", [_build_zip, _build_tar], ids=["zip", "tar"])
def test_extracts_legitimate_members(tmp_path, proj_path, build_archive):
    src = build_archive(tmp_path, ["projroot/", "projroot/file.txt", "projroot/sub/", "projroot/sub/nested.txt"])
    action = make_action_module(src, proj_path)

    result = action.run()

    assert result.get("failed") is not True
    assert result["changed"] is True
    assert os.path.isfile(os.path.join(proj_path, "file.txt"))
    assert os.path.isfile(os.path.join(proj_path, "sub/nested.txt"))


@pytest.mark.parametrize("build_archive", [_build_zip, _build_tar], ids=["zip", "tar"])
class TestRunRejectsUnsafeMembers:
    # The guard that catches UnsafeArchivePathError and fails the task lives in
    # run() after the archive-format branch, so it behaves identically for zip
    # and tar - these are parametrized rather than duplicated per format.

    def test_rejects_traversal_member_and_writes_nothing_outside(self, tmp_path, proj_path, build_archive):
        src = build_archive(tmp_path, ["projroot/", "projroot/../../../../tmp/evil.txt"])
        action = make_action_module(src, proj_path)

        result = action.run()

        assert result.get("failed") is True
        assert "outside of the project path" in result.get("msg", "")
        assert os.listdir(proj_path) == []

    def test_rejects_absolute_path_member(self, tmp_path, proj_path, build_archive):
        # Two distinct top-level names prevent the "single common root directory"
        # detection from stripping the leading '/' off the malicious member.
        src = build_archive(tmp_path, ["safe.txt", "/etc/evil.txt"])
        action = make_action_module(src, proj_path)

        result = action.run()

        assert result.get("failed") is True
        assert "not allowed" in result.get("msg", "")
        assert not os.path.exists("/etc/evil.txt")
