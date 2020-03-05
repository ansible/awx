import ast
import warnings
import py.path
import pytest
import six

from ansible.parsing.metadata import extract_metadata

from .conftest import TEST_PLAYBOOKS

if six.PY2:
    ast_try = ast.TryExcept
else:
    ast_try = ast.Try

MODULES_PATH = py.path.local(__file__).realpath() / '..' / '..' / 'plugins' / 'modules'


def find_all_modules():
    for module in MODULES_PATH.listdir(sort=True):
        module = module.basename.replace('.py', '')
        if module != '__init__':
            yield module


ALL_MODULES = list(find_all_modules())


def _strip_module_prefix(module):
    return module.replace('foreman_', '').replace('katello_', '')


def _module_file_path(module):
    module_file_name = "{}.py".format(module)
    return MODULES_PATH / module_file_name


def _module_is_tested(module):
    short_module = _strip_module_prefix(module)
    return short_module in TEST_PLAYBOOKS or module in TEST_PLAYBOOKS


def _module_framework(module):
    module_file_path = _module_file_path(module)
    with module_file_path.open() as module_file:
        module_ast = ast.parse(module_file.read())
    return _module_framework_from_body(module_ast.body) or 'unknown'


def _module_framework_from_body(body):
    framework = None
    for entry in body:
        if isinstance(entry, ast.ImportFrom):
            if entry.module == 'ansible.module_utils.foreman_helper' and not framework:
                framework = 'apypie'
        elif isinstance(entry, ast_try) and not framework:
            framework = _module_framework_from_body(entry.body)
    return framework


def _module_is_deprecated(module):
    module_file_path = _module_file_path(module)
    with module_file_path.open() as module_file:
        metadata = extract_metadata(module_data=module_file.read())
    if metadata[0]:
        return 'deprecated' in metadata[0].get('status', [])
    else:
        return False


def generate_tested_report():
    print("# tested modules")
    for module in ALL_MODULES:
        if _module_is_tested(module):
            x = 'x'
        else:
            x = ' '
        extra = []
        if _module_is_deprecated(module):
            extra.append('deprecated')
        if extra:
            extra = ' ({})'.format(','.join(extra))
        else:
            extra = ''
        print("- [{}] {}{}".format(x, module, extra))
    print("")


def generate_apypie_report():
    print("# modules migrated to apypie")
    for module in ALL_MODULES:
        if _module_framework(module) == 'apypie' or module == 'redhat_manifest':
            x = 'x'
        else:
            x = ' '
        extra = []
        if _module_is_deprecated(module):
            extra.append('deprecated')
        if extra:
            extra = ' ({})'.format(','.join(extra))
        else:
            extra = ''
        print("- [{}] {}{}".format(x, module, extra))
    print("")


@pytest.mark.parametrize('module', ALL_MODULES)
def test_module_framework(module):
    module_framework = _module_framework(module)
    assert (module_framework == 'apypie' or module == 'redhat_manifest')


@pytest.mark.parametrize('module', ALL_MODULES)
def test_module_state(module):
    if _module_is_deprecated(module):
        warnings.warn("{} is deprecated".format(module))
    else:
        assert _module_is_tested(module)


if __name__ == '__main__':
    generate_tested_report()
    generate_apypie_report()
