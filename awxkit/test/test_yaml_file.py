import io
import os

import pytest
import yaml

from awxkit.exceptions import PathTraversalError
from awxkit.yaml_file import Loader, file_path_cache, file_pattern_cache, load_file


@pytest.fixture(autouse=True)
def clear_yaml_caches():
    file_pattern_cache.clear()
    file_path_cache.clear()
    yield
    file_pattern_cache.clear()
    file_path_cache.clear()


@pytest.fixture
def yaml_tree(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    sub = project / "sub"
    sub.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    (project / "main.yaml").write_text("key: value\n")
    (sub / "included.yaml").write_text("included_key: included_value\n")
    (sub / "nested.yaml").write_text("nested_key: nested_value\n")
    (outside / "secret.yaml").write_text("secret: exposed\n")

    return project


def load_yaml_with_root(content, root_dir):
    stream = io.StringIO(content)
    stream.name = os.path.join(root_dir, "test_input.yaml")
    return yaml.load(stream, Loader=Loader)


def load_yaml_as_stdin(content):
    stream = io.StringIO(content)
    stream.name = "<stdin>"
    return yaml.load(stream, Loader=Loader)


class TestIncludeLegitimate:
    def test_relative_same_directory(self, yaml_tree):
        result = load_yaml_with_root("data: !include sub/included.yaml", str(yaml_tree))
        assert result["data"]["included_key"] == "included_value"

    def test_glob_within_tree(self, yaml_tree):
        result = load_yaml_with_root("data: !include sub/*.yaml", str(yaml_tree))
        assert "included_key" in result["data"]
        assert "nested_key" in result["data"]

    def test_sequence_node(self, yaml_tree):
        content = "data: !include\n  - sub/included.yaml\n  - sub/nested.yaml\n"
        result = load_yaml_with_root(content, str(yaml_tree))
        assert "included_key" in result["data"]
        assert "nested_key" in result["data"]

    def test_mapping_node(self, yaml_tree):
        content = "data: !include\n  included_key: sub/included.yaml\n  nested_key: sub/nested.yaml\n"
        result = load_yaml_with_root(content, str(yaml_tree))
        assert result["data"]["included_key"] == "included_value"
        assert result["data"]["nested_key"] == "nested_value"

    def test_load_file_with_include(self, yaml_tree):
        main_yaml = yaml_tree / "main_with_include.yaml"
        main_yaml.write_text("imported: !include sub/included.yaml\n")
        result = load_file(str(main_yaml))
        assert result["imported"]["included_key"] == "included_value"

    def test_relative_filename_with_no_directory_component(self, yaml_tree, monkeypatch):
        # A stream.name with no directory component (e.g. `open("main.yaml")` from cwd)
        # must still resolve _root to cwd, not be mistaken for stdin.
        monkeypatch.chdir(yaml_tree)
        stream = io.StringIO("data: !include sub/included.yaml")
        stream.name = "main.yaml"
        result = yaml.load(stream, Loader=Loader)
        assert result["data"]["included_key"] == "included_value"


class TestIncludePathTraversal:
    def test_relative_traversal(self, yaml_tree):
        with pytest.raises(PathTraversalError):
            load_yaml_with_root("data: !include ../outside/secret.yaml", str(yaml_tree))

    def test_dotdot_deeper(self, yaml_tree):
        with pytest.raises(PathTraversalError):
            load_yaml_with_root("data: !include ../../etc/passwd", str(yaml_tree))

    def test_absolute_path(self, yaml_tree):
        with pytest.raises(PathTraversalError):
            load_yaml_with_root("data: !include /etc/passwd", str(yaml_tree))

    def test_glob_traversal(self, yaml_tree):
        with pytest.raises(PathTraversalError):
            load_yaml_with_root("data: !include ../outside/*.yaml", str(yaml_tree))

    def test_stdin_rejected(self):
        with pytest.raises(PathTraversalError, match="stdin"):
            load_yaml_as_stdin("data: !include some_file.yaml")

    def test_symlink_escape(self, yaml_tree, tmp_path):
        outside_file = tmp_path / "outside" / "secret.yaml"
        symlink = yaml_tree / "sub" / "link_to_outside.yaml"
        symlink.symlink_to(outside_file)

        with pytest.raises(PathTraversalError):
            load_yaml_with_root("data: !include sub/link_to_outside.yaml", str(yaml_tree))

    def test_traversal_in_sequence(self, yaml_tree):
        content = "data: !include\n  - sub/included.yaml\n  - ../outside/secret.yaml\n"
        with pytest.raises(PathTraversalError):
            load_yaml_with_root(content, str(yaml_tree))

    def test_error_message_says_not_allowed(self, yaml_tree):
        with pytest.raises(PathTraversalError, match="not allowed"):
            load_yaml_with_root("data: !include ../outside/secret.yaml", str(yaml_tree))

    def test_traversal_in_mapping_value(self, yaml_tree):
        content = "data: !include\n  included_key: ../outside/secret.yaml\n"
        with pytest.raises(PathTraversalError):
            load_yaml_with_root(content, str(yaml_tree))

    def test_symlink_directory_escape(self, yaml_tree, tmp_path):
        outside_dir = tmp_path / "outside"
        link_dir = yaml_tree / "sub" / "link_to_outside"
        link_dir.symlink_to(outside_dir)

        with pytest.raises(PathTraversalError):
            load_yaml_with_root("data: !include sub/link_to_outside/secret.yaml", str(yaml_tree))

    def test_load_file_with_traversal(self, yaml_tree):
        malicious = yaml_tree / "malicious.yaml"
        malicious.write_text("exploit: !include ../outside/secret.yaml\n")
        with pytest.raises(PathTraversalError):
            load_file(str(malicious))

    def test_error_message_absolute_path(self):
        stream = io.StringIO("data: !include /etc/passwd")
        stream.name = "/some/dir/test.yaml"
        with pytest.raises(PathTraversalError, match="not allowed"):
            yaml.load(stream, Loader=Loader)
