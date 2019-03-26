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

TEST_SOURCE_FIELDS = {
    'vmware': {
        'instance_filters': 'foobaa',
        'group_by': 'fouo'
    },
    'ec2': {
        'instance_filters': 'foobaa',
        # group_by selected to capture some non-trivial cross-interactions
        'group_by': 'availability_zone,instance_type,tag_keys,region',
        'source_regions': 'us-east-2,ap-south-1'
    },
    'gce': {
        'source_regions': 'us-east4-a,us-west1-b'  # surfaced as env var
    },
    'azure_rm': {
        'source_regions': 'southcentralus,westus'
    },
    'tower': {
        'instance_filters': '42'
    }
}

INI_TEST_VARS = {
    'ec2': {
        'boto_profile': '/tmp/my_boto_stuff'
    },
    'gce': {},
    'openstack': {
        'private': False,
        'use_hostnames': False,
        'expand_hostvars': True,
        'fail_on_errors': True
    },
    'rhv': {},  # there are none
    'tower': {},  # there are none
    'vmware': {
        # setting VMWARE_VALIDATE_CERTS is duplicated with env var
    },
    'azure_rm': {
        'use_private_ip': True,
        'resource_groups': 'foo_resources,bar_resources'
    },
    'satellite6': {
        'satellite6_group_patterns': 'foo_group_patterns',
        'satellite6_group_prefix': 'foo_group_prefix',
        'satellite6_want_hostcollections': True
    },
    'cloudforms': {
        'version': '2.4',
        'purge_actions': 'maybe',
        'clean_group_keys': 'this_key',
        'nest_tags': 'yes',
        'suffix': '.ppt',
        'prefer_ipv4': 'yes'
    }
}


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
def fake_credential_factory(source):
    ct = CredentialType.defaults[credential_kind(source)]()
    ct.save()

    inputs = {}
    var_specs = {}  # pivoted version of inputs
    for element in ct.inputs.get('fields'):
        var_specs[element['id']] = element
    for var in var_specs.keys():
        inputs[var] = generate_fake_var(var_specs[var])

    return Credential.objects.create(
        credential_type=ct,
        inputs=inputs
    )


def read_content(private_data_dir, raw_env, inventory_update):
    """Read the environmental data laid down by the task system
    template out private and secret data so they will be readable and predictable
    return a dictionary `content` with file contents, keyed off environment variable
        that references the file
    """
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
        inverse_env[value] = key

    cache_file_regex = re.compile(r'/tmp/awx_{0}_[a-zA-Z0-9_]+/{1}_cache[a-zA-Z0-9_]+'.format(
        inventory_update.id, inventory_update.source)
    )
    private_key_regex = re.compile(r'-----BEGIN ENCRYPTED PRIVATE KEY-----.*-----END ENCRYPTED PRIVATE KEY-----')

    dir_contents = {}
    references = {}
    for filename in os.listdir(private_data_dir):
        if filename in ('args', 'project'):
            continue  # Ansible runner
        abs_file_path = os.path.join(private_data_dir, filename)
        if abs_file_path in inverse_env:
            env_key = inverse_env[abs_file_path]
            references[abs_file_path] = env_key
            env[env_key] = '{{ file_reference }}'
        try:
            with open(abs_file_path, 'r') as f:
                dir_contents[abs_file_path] = f.read()
            # Declare a reference to inventory plugin file if it exists
            if abs_file_path.endswith('.yml') and 'plugin: ' in dir_contents[abs_file_path]:
                references[abs_file_path] = filename  # plugin filenames are universal
        except IsADirectoryError:
            dir_contents[abs_file_path] = '<directory>'

    # Declare cross-file references, also use special keywords if it is the cache
    cache_referenced = False
    cache_present = False
    for abs_file_path, file_content in dir_contents.copy().items():
        if cache_file_regex.match(file_content):
            cache_referenced = True
        for target_path in dir_contents.keys():
            if target_path in file_content:
                if target_path in references:
                    raise AssertionError(
                        'File {} is referenced by env var or other file as well as file {}:\n{}\n{}'.format(
                            target_path, abs_file_path, json.dumps(env, indent=4), json.dumps(dir_contents, indent=4)))
                else:
                    if cache_file_regex.match(target_path):
                        cache_present = True
                        if os.path.isdir(target_path):
                            keyword = 'cache_dir'
                        else:
                            keyword = 'cache_file'
                        references[target_path] = keyword
                        new_file_content = cache_file_regex.sub('{{ ' + keyword + ' }}', file_content)
                    else:
                        references[target_path] = 'file_reference'
                        new_file_content = file_content.replace(target_path, '{{ file_reference }}')
                    dir_contents[abs_file_path] = new_file_content
    if cache_referenced and not cache_present:
        raise AssertionError(
            'A cache file was referenced but never created, files:\n{}'.format(
                json.dumps(dir_contents, indent=4)))

    content = {}
    for abs_file_path, file_content in dir_contents.items():
        if abs_file_path not in references:
            raise AssertionError(
                "File {} is not referenced. References and files:\n{}\n{}".format(
                    abs_file_path, json.dumps(references, indent=4), json.dumps(dir_contents, indent=4)))
        reference_key = references[abs_file_path]
        file_content = private_key_regex.sub('{{private_key}}', file_content)
        content[reference_key] = file_content

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
            f.write(json.dumps(env, indent=4))


@pytest.mark.django_db
@pytest.mark.parametrize('this_kind', CLOUD_PROVIDERS)
@pytest.mark.parametrize('script_or_plugin', ['scripts', 'plugins'])
def test_inventory_update_injected_content(this_kind, script_or_plugin, inventory):
    src_vars = dict(base_source_var='value_of_var')
    if this_kind in INI_TEST_VARS:
        src_vars.update(INI_TEST_VARS[this_kind])
    extra_kwargs = {}
    if this_kind in TEST_SOURCE_FIELDS:
        extra_kwargs.update(TEST_SOURCE_FIELDS[this_kind])
    inventory_source = InventorySource.objects.create(
        inventory=inventory,
        source=this_kind,
        source_vars=src_vars,
        **extra_kwargs
    )
    inventory_source.credentials.add(fake_credential_factory(this_kind))
    inventory_update = inventory_source.create_unified_job()
    task = RunInventoryUpdate()

    use_plugin = bool(script_or_plugin == 'plugins')
    if use_plugin and InventorySource.injectors[this_kind].plugin_name is None:
        pytest.skip('Use of inventory plugin is not enabled for this source')

    def substitute_run(envvars=None, **_kw):
        """This method will replace run_pexpect
        instead of running, it will read the private data directory contents
        It will make assertions that the contents are correct
        If MAKE_INVENTORY_REFERENCE_FILES is set, it will produce reference files
        """
        private_data_dir = envvars.pop('AWX_PRIVATE_DATA_DIR')
        assert envvars.pop('ANSIBLE_INVENTORY_ENABLED') == ('auto' if use_plugin else 'script')
        set_files = bool(os.getenv("MAKE_INVENTORY_REFERENCE_FILES", 'false').lower()[0] not in ['f', '0'])
        env, content = read_content(private_data_dir, envvars, inventory_update)
        base_dir = os.path.join(DATA, script_or_plugin)
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)
        source_dir = os.path.join(base_dir, this_kind)  # this_kind is a global
        if set_files:
            create_reference_data(source_dir, env, content)
            pytest.skip('You set MAKE_INVENTORY_REFERENCE_FILES, so this created files, unset to run actual test.')
        else:
            if not os.path.exists(source_dir):
                raise FileNotFoundError(
                    'Maybe you never made reference files? '
                    'MAKE_INVENTORY_REFERENCE_FILES=true py.test ...\noriginal: {}')
            files_dir = os.path.join(source_dir, 'files')
            try:
                expected_file_list = os.listdir(files_dir)
            except FileNotFoundError:
                expected_file_list = []
            assert set(expected_file_list) == set(content.keys()), (
                'Inventory update runtime environment does not have expected files'
            )
            for f_name in expected_file_list:
                with open(os.path.join(files_dir, f_name), 'r') as f:
                    ref_content = f.read()
                    assert ref_content == content[f_name]
            try:
                with open(os.path.join(source_dir, 'env.json'), 'r') as f:
                    ref_env_text = f.read()
                    ref_env = json.loads(ref_env_text)
            except FileNotFoundError:
                ref_env = {}
            assert ref_env == env
        Res = namedtuple('Result', ['status', 'rc'])
        return Res('successful', 0)

    mock_licenser = mock.Mock(return_value=mock.Mock(
        validate=mock.Mock(return_value={'license_type': 'open'})
    ))

    # Mock this so that it will not send events to the callback receiver
    # because doing so in pytest land creates large explosions
    with mock.patch('awx.main.queue.CallbackQueueDispatcher.dispatch', lambda self, obj: None):
        # Force the update to use the script injector
        with mock.patch('awx.main.models.inventory.PluginFileInjector.should_use_plugin', return_value=use_plugin):
            # Also do not send websocket status updates
            with mock.patch.object(UnifiedJob, 'websocket_emit_status', mock.Mock()):
                # The point of this test is that we replace run with assertions
                with mock.patch('awx.main.tasks.ansible_runner.interface.run', substitute_run):
                    # mocking the licenser is necessary for the tower source
                    with mock.patch('awx.main.models.inventory.get_licenser', mock_licenser):
                        # so this sets up everything for a run and then yields control over to substitute_run
                        task.run(inventory_update.pk)
