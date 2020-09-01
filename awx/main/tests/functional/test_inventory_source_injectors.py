import pytest
from unittest import mock
import os
import json
import re
from collections import namedtuple

from awx.main.tasks import RunInventoryUpdate
from awx.main.models import InventorySource, Credential, CredentialType, UnifiedJob
from awx.main.constants import CLOUD_PROVIDERS, STANDARD_INVENTORY_UPDATE_ENV
from awx.main.tests import data

from django.conf import settings

DATA = os.path.join(os.path.dirname(data.__file__), 'inventory')


def generate_fake_var(element):
    """Given a credential type field element, makes up something acceptable.
    """
    if element['type'] == 'string':
        if element.get('format', None) == 'ssh_private_key':
            # this example came from the internet
            return '\n'.join([
                '-----BEGIN ENCRYPTED PRIVATE KEY-----'
                'MIIBpjBABgkqhkiG9w0BBQ0wMzAbBgkqhkiG9w0BBQwwDgQI5yNCu9T5SnsCAggA'
                'MBQGCCqGSIb3DQMHBAhJISTgOAxtYwSCAWDXK/a1lxHIbRZHud1tfRMR4ROqkmr4'
                'kVGAnfqTyGptZUt3ZtBgrYlFAaZ1z0wxnhmhn3KIbqebI4w0cIL/3tmQ6eBD1Ad1'
                'nSEjUxZCuzTkimXQ88wZLzIS9KHc8GhINiUu5rKWbyvWA13Ykc0w65Ot5MSw3cQc'
                'w1LEDJjTculyDcRQgiRfKH5376qTzukileeTrNebNq+wbhY1kEPAHojercB7d10E'
                '+QcbjJX1Tb1Zangom1qH9t/pepmV0Hn4EMzDs6DS2SWTffTddTY4dQzvksmLkP+J'
                'i8hkFIZwUkWpT9/k7MeklgtTiy0lR/Jj9CxAIQVxP8alLWbIqwCNRApleSmqtitt'
                'Z+NdsuNeTm3iUaPGYSw237tjLyVE6pr0EJqLv7VUClvJvBnH2qhQEtWYB9gvE1dS'
                'BioGu40pXVfjiLqhEKVVVEoHpI32oMkojhCGJs8Oow4bAxkzQFCtuWB1'
                '-----END ENCRYPTED PRIVATE KEY-----'
            ])
        if element['id'] == 'host':
            return 'https://foo.invalid'
        return 'fooo'
    elif element['type'] == 'boolean':
        return False
    raise Exception('No generator written for {} type'.format(element.get('type', 'unknown')))


def credential_kind(source):
    """Given the inventory source kind, return expected credential kind
    """
    return source.replace('ec2', 'aws')


@pytest.fixture
def fake_credential_factory():
    def wrap(source):
        ct = CredentialType.defaults[credential_kind(source)]()
        ct.save()

        inputs = {}
        var_specs = {}  # pivoted version of inputs
        for element in ct.inputs.get('fields'):
            var_specs[element['id']] = element
        for var in var_specs.keys():
            inputs[var] = generate_fake_var(var_specs[var])

        if source == 'tower':
            inputs.pop('oauth_token')  # mutually exclusive with user/pass

        return Credential.objects.create(
            credential_type=ct,
            inputs=inputs
        )
    return wrap



def read_content(private_data_dir, raw_env, inventory_update):
    """Read the environmental data laid down by the task system
    template out private and secret data so they will be readable and predictable
    return a dictionary `content` with file contents, keyed off environment variable
        that references the file
    """
    # build dict env as a mapping of environment variables to file names
    # Filter out environment variables which come from runtime environment
    env = {}
    exclude_keys = set(('PATH', 'INVENTORY_SOURCE_ID', 'INVENTORY_UPDATE_ID'))
    for key in dir(settings):
        if key.startswith('ANSIBLE_'):
            exclude_keys.add(key)
    for k, v in raw_env.items():
        if k in STANDARD_INVENTORY_UPDATE_ENV or k in exclude_keys:
            continue
        if k not in os.environ or v != os.environ[k]:
            env[k] = v
    inverse_env = {}
    for key, value in env.items():
        inverse_env.setdefault(value, []).append(key)

    cache_file_regex = re.compile(r'/tmp/awx_{0}_[a-zA-Z0-9_]+/{1}_cache[a-zA-Z0-9_]+'.format(
        inventory_update.id, inventory_update.source)
    )
    private_key_regex = re.compile(r'-----BEGIN ENCRYPTED PRIVATE KEY-----.*-----END ENCRYPTED PRIVATE KEY-----')

    # read directory content
    # build a mapping of the file paths to aliases which will be constant accross runs
    dir_contents = {}
    referenced_paths = set()
    file_aliases = {}
    filename_list = sorted(os.listdir(private_data_dir), key=lambda fn: inverse_env.get(os.path.join(private_data_dir, fn), [fn])[0])
    for filename in filename_list:
        if filename in ('args', 'project'):
            continue  # Ansible runner
        abs_file_path = os.path.join(private_data_dir, filename)
        file_aliases[abs_file_path] = filename
        if abs_file_path in inverse_env:
            referenced_paths.add(abs_file_path)
            alias = 'file_reference'
            for i in range(10):
                if alias not in file_aliases.values():
                    break
                alias = 'file_reference_{}'.format(i)
            else:
                raise RuntimeError('Test not able to cope with >10 references by env vars. '
                                   'Something probably went very wrong.')
            file_aliases[abs_file_path] = alias
            for env_key in inverse_env[abs_file_path]:
                env[env_key] = '{{{{ {} }}}}'.format(alias)
        try:
            with open(abs_file_path, 'r') as f:
                dir_contents[abs_file_path] = f.read()
            # Declare a reference to inventory plugin file if it exists
            if abs_file_path.endswith('.yml') and 'plugin: ' in dir_contents[abs_file_path]:
                referenced_paths.add(abs_file_path)  # used as inventory file
            elif cache_file_regex.match(abs_file_path):
                file_aliases[abs_file_path] = 'cache_file'
        except IsADirectoryError:
            dir_contents[abs_file_path] = '<directory>'
            if cache_file_regex.match(abs_file_path):
                file_aliases[abs_file_path] = 'cache_dir'

    # Substitute in aliases for cross-file references
    for abs_file_path, file_content in dir_contents.copy().items():
        if cache_file_regex.match(file_content):
            if 'cache_dir' not in file_aliases.values() and 'cache_file' not in file_aliases in file_aliases.values():
                raise AssertionError(
                    'A cache file was referenced but never created, files:\n{}'.format(
                        json.dumps(dir_contents, indent=4)))
        # if another files path appears in this file, replace it with its alias
        for target_path in dir_contents.keys():
            other_alias = file_aliases[target_path]
            if target_path in file_content:
                referenced_paths.add(target_path)
                dir_contents[abs_file_path] = file_content.replace(target_path, '{{ ' + other_alias + ' }}')

    # build dict content which is the directory contents keyed off the file aliases
    content = {}
    for abs_file_path, file_content in dir_contents.items():
        # assert that all files laid down are used
        if abs_file_path not in referenced_paths:
            raise AssertionError(
                "File {} is not referenced. References and files:\n{}\n{}".format(
                    abs_file_path, json.dumps(env, indent=4), json.dumps(dir_contents, indent=4)))
        file_content = private_key_regex.sub('{{private_key}}', file_content)
        content[file_aliases[abs_file_path]] = file_content

    return (env, content)


def create_reference_data(source_dir, env, content):
    if not os.path.exists(source_dir):
        os.mkdir(source_dir)
    if content:
        files_dir = os.path.join(source_dir, 'files')
        if not os.path.exists(files_dir):
            os.mkdir(files_dir)
        for env_name, content in content.items():
            with open(os.path.join(files_dir, env_name), 'w') as f:
                f.write(content)
    if env:
        with open(os.path.join(source_dir, 'env.json'), 'w') as f:
            json.dump(env, f, indent=4, sort_keys=True)


@pytest.mark.django_db
@pytest.mark.parametrize('this_kind', CLOUD_PROVIDERS)
def test_inventory_update_injected_content(this_kind, inventory, fake_credential_factory):
    injector = InventorySource.injectors[this_kind]
    if injector.plugin_name is None:
        pytest.skip('Use of inventory plugin is not enabled for this source')

    src_vars = dict(base_source_var='value_of_var')
    src_vars['plugin'] = injector.get_proper_name()
    inventory_source = InventorySource.objects.create(
        inventory=inventory,
        source=this_kind,
        source_vars=src_vars,
    )
    inventory_source.credentials.add(fake_credential_factory(this_kind))
    inventory_update = inventory_source.create_unified_job()
    task = RunInventoryUpdate()

    def substitute_run(envvars=None, **_kw):
        """This method will replace run_pexpect
        instead of running, it will read the private data directory contents
        It will make assertions that the contents are correct
        If MAKE_INVENTORY_REFERENCE_FILES is set, it will produce reference files
        """
        private_data_dir = envvars.pop('AWX_PRIVATE_DATA_DIR')
        assert envvars.pop('ANSIBLE_INVENTORY_ENABLED') == 'auto'
        set_files = bool(os.getenv("MAKE_INVENTORY_REFERENCE_FILES", 'false').lower()[0] not in ['f', '0'])
        env, content = read_content(private_data_dir, envvars, inventory_update)

        # Assert inventory plugin inventory file is in private_data_dir
        inventory_filename = InventorySource.injectors[inventory_update.source]().filename
        assert len([True for k in content.keys() if k.endswith(inventory_filename)]) > 0, \
            f"'{inventory_filename}' file not found in inventory update runtime files {content.keys()}"

        env.pop('ANSIBLE_COLLECTIONS_PATHS', None)  # collection paths not relevant to this test
        base_dir = os.path.join(DATA, 'plugins')
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)
        source_dir = os.path.join(base_dir, this_kind)  # this_kind is a global
        if set_files:
            create_reference_data(source_dir, env, content)
            pytest.skip('You set MAKE_INVENTORY_REFERENCE_FILES, so this created files, unset to run actual test.')
        else:
            source_dir = os.path.join(base_dir, this_kind)  # this_kind is a global

            if not os.path.exists(source_dir):
                raise FileNotFoundError(
                    'Maybe you never made reference files? '
                    'MAKE_INVENTORY_REFERENCE_FILES=true py.test ...\noriginal: {}')
            files_dir = os.path.join(source_dir, 'files')
            try:
                expected_file_list = os.listdir(files_dir)
            except FileNotFoundError:
                expected_file_list = []
            for f_name in expected_file_list:
                with open(os.path.join(files_dir, f_name), 'r') as f:
                    ref_content = f.read()
                    assert ref_content == content[f_name], f_name
            try:
                with open(os.path.join(source_dir, 'env.json'), 'r') as f:
                    ref_env_text = f.read()
                    ref_env = json.loads(ref_env_text)
            except FileNotFoundError:
                ref_env = {}
            assert ref_env == env
        Res = namedtuple('Result', ['status', 'rc'])
        return Res('successful', 0)

    # Mock this so that it will not send events to the callback receiver
    # because doing so in pytest land creates large explosions
    with mock.patch('awx.main.queue.CallbackQueueDispatcher.dispatch', lambda self, obj: None):
        # Also do not send websocket status updates
        with mock.patch.object(UnifiedJob, 'websocket_emit_status', mock.Mock()):
            # The point of this test is that we replace run with assertions
            with mock.patch('awx.main.tasks.ansible_runner.interface.run', substitute_run):
                # so this sets up everything for a run and then yields control over to substitute_run
                task.run(inventory_update.pk)
