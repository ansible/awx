# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

from __future__ import absolute_import

from collections import OrderedDict
import json
import os
import shutil
import sys
import tempfile
from unittest import mock

import pytest

# ansible uses `ANSIBLE_CALLBACK_PLUGINS` and `ANSIBLE_STDOUT_CALLBACK` to
# discover callback plugins;  `ANSIBLE_CALLBACK_PLUGINS` is a list of paths to
# search for a plugin implementation (which should be named `CallbackModule`)
#
# this code modifies the Python path to make our
# `awx.lib.awx_display_callback` callback importable (because `awx.lib`
# itself is not a package)
#
# we use the `awx_display_callback` imports below within this file, but
# Ansible also uses them when it discovers this file in
# `ANSIBLE_CALLBACK_PLUGINS`
CALLBACK = os.path.splitext(os.path.basename(__file__))[0]
PLUGINS = os.path.dirname(__file__)
with mock.patch.dict(os.environ, {'ANSIBLE_STDOUT_CALLBACK': CALLBACK,
                                  'ANSIBLE_CALLBACK_PLUGINS': PLUGINS}):
    from ansible import __version__ as ANSIBLE_VERSION
    from ansible.cli.playbook import PlaybookCLI
    from ansible.executor.playbook_executor import PlaybookExecutor
    from ansible.inventory.manager import InventoryManager
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager

    # Add awx/lib to sys.path so we can use the plugin
    path = os.path.abspath(os.path.join(PLUGINS, '..', '..', 'lib'))
    if path not in sys.path:
        sys.path.insert(0, path)

    from awx_display_callback import AWXDefaultCallbackModule as CallbackModule  # noqa
    from awx_display_callback.events import event_context  # noqa


@pytest.fixture()
def cache(request):
    class Cache(OrderedDict):
        def set(self, key, value):
            self[key] = value
    local_cache = Cache()
    patch = mock.patch.object(event_context, 'cache', local_cache)
    patch.start()
    request.addfinalizer(patch.stop)
    return local_cache


@pytest.fixture()
def executor(tmpdir_factory, request):
    playbooks = request.node.callspec.params.get('playbook')
    playbook_files = []
    for name, playbook in playbooks.items():
        filename = str(tmpdir_factory.mktemp('data').join(name))
        with open(filename, 'w') as f:
            f.write(playbook)
        playbook_files.append(filename)

    cli = PlaybookCLI(['', 'playbook.yml'])
    cli.parse()
    options = cli.parser.parse_args(['-v'])[0]
    loader = DataLoader()
    variable_manager = VariableManager(loader=loader)
    inventory = InventoryManager(loader=loader, sources='localhost,')
    variable_manager.set_inventory(inventory)

    return PlaybookExecutor(playbooks=playbook_files, inventory=inventory,
                            variable_manager=variable_manager, loader=loader,
                            options=options, passwords={})


@pytest.mark.parametrize('event', {'playbook_on_start',
                                   'playbook_on_play_start',
                                   'playbook_on_task_start', 'runner_on_ok',
                                   'playbook_on_stats'})
@pytest.mark.parametrize('playbook', [
{'helloworld.yml': '''
- name: Hello World Sample
  connection: local
  hosts: all
  gather_facts: no
  tasks:
    - name: Hello Message
      debug:
        msg: "Hello World!"
'''},  # noqa
{'results_included.yml': '''
- name: Run module which generates results list
  connection: local
  hosts: all
  gather_facts: no
  vars:
    results: ['foo', 'bar']
  tasks:
    - name: Generate results list
      debug:
        var: results
'''},  # noqa
])
def test_callback_plugin_receives_events(executor, cache, event, playbook):
    executor.run()
    assert len(cache)
    assert event in [task['event'] for task in cache.values()]


@pytest.mark.parametrize('playbook', [
{'no_log_on_ok.yml': '''
- name: args should not be logged when task-level no_log is set
  connection: local
  hosts: all
  gather_facts: no
  tasks:
    - shell: echo "SENSITIVE"
      no_log: true
'''},  # noqa
{'no_log_on_fail.yml': '''
- name: failed args should not be logged when task-level no_log is set
  connection: local
  hosts: all
  gather_facts: no
  tasks:
    - shell: echo "SENSITIVE"
      no_log: true
      failed_when: true
      ignore_errors: true
'''},  # noqa
{'no_log_on_skip.yml': '''
- name: skipped task args should be suppressed with no_log
  connection: local
  hosts: all
  gather_facts: no
  tasks:
    - shell: echo "SENSITIVE"
      no_log: true
      when: false
'''},  # noqa
{'no_log_on_play.yml': '''
- name: args should not be logged when play-level no_log set
  connection: local
  hosts: all
  gather_facts: no
  no_log: true
  tasks:
      - shell: echo "SENSITIVE"
'''},  # noqa
{'async_no_log.yml': '''
- name: async task args should suppressed with no_log
  connection: local
  hosts: all
  gather_facts: no
  no_log: true
  tasks:
    - async: 10
      poll: 1
      shell: echo "SENSITIVE"
      no_log: true
'''},  # noqa
{'with_items.yml': '''
- name: with_items tasks should be suppressed with no_log
  connection: local
  hosts: all
  gather_facts: no
  tasks:
      - shell: echo {{ item }}
        no_log: true
        with_items: [ "SENSITIVE", "SENSITIVE-SKIPPED", "SENSITIVE-FAILED" ]
        when: item != "SENSITIVE-SKIPPED"
        failed_when: item == "SENSITIVE-FAILED"
        ignore_errors: yes
'''},  # noqa, NOTE: with_items will be deprecated in 2.9
{'loop.yml': '''
- name: loop tasks should be suppressed with no_log
  connection: local
  hosts: all
  gather_facts: no
  tasks:
      - shell: echo {{ item }}
        no_log: true
        loop: [ "SENSITIVE", "SENSITIVE-SKIPPED", "SENSITIVE-FAILED" ]
        when: item != "SENSITIVE-SKIPPED"
        failed_when: item == "SENSITIVE-FAILED"
        ignore_errors: yes
'''},  # noqa
])
def test_callback_plugin_no_log_filters(executor, cache, playbook):
    executor.run()
    assert len(cache)
    assert 'SENSITIVE' not in json.dumps(cache.items())


@pytest.mark.parametrize('playbook', [
{'no_log_on_ok.yml': '''
- name: args should not be logged when no_log is set at the task or module level
  connection: local
  hosts: all
  gather_facts: no
  tasks:
    - shell: echo "PUBLIC"
    - shell: echo "PRIVATE"
      no_log: true
    - uri: url=https://example.org username="PUBLIC" password="PRIVATE"
    - copy: content="PRIVATE" dest="/tmp/tmp_no_log"
'''},  # noqa
])
def test_callback_plugin_task_args_leak(executor, cache, playbook):
    executor.run()
    events = cache.values()
    assert events[0]['event'] == 'playbook_on_start'
    assert events[1]['event'] == 'playbook_on_play_start'

    # task 1
    assert events[2]['event'] == 'playbook_on_task_start'
    assert events[3]['event'] == 'runner_on_ok'

    # task 2 no_log=True
    assert events[4]['event'] == 'playbook_on_task_start'
    assert events[5]['event'] == 'runner_on_ok'
    assert 'PUBLIC' in json.dumps(cache.items())
    assert 'PRIVATE' not in json.dumps(cache.items())
    # make sure playbook was successful, so all tasks were hit
    assert not events[-1]['event_data']['failures'], 'Unexpected playbook execution failure'


@pytest.mark.parametrize('playbook', [
{'loop_with_no_log.yml': '''
- name: playbook variable should not be overwritten when using no log
  connection: local
  hosts: all
  gather_facts: no
  tasks:
    - command: "{{ item }}"
      register: command_register
      no_log: True
      with_items:
        - "echo helloworld!"
    - debug: msg="{{ command_register.results|map(attribute='stdout')|list }}"
'''},  # noqa
])
def test_callback_plugin_censoring_does_not_overwrite(executor, cache, playbook):
    executor.run()
    events = cache.values()
    assert events[0]['event'] == 'playbook_on_start'
    assert events[1]['event'] == 'playbook_on_play_start'

    # task 1
    assert events[2]['event'] == 'playbook_on_task_start'
    # Ordering of task and item events may differ randomly
    assert set(['runner_on_ok', 'runner_item_on_ok']) == set([data['event'] for data in events[3:5]])

    # task 2 no_log=True
    assert events[5]['event'] == 'playbook_on_task_start'
    assert events[6]['event'] == 'runner_on_ok'
    assert 'helloworld!' in events[6]['event_data']['res']['msg']


@pytest.mark.parametrize('playbook', [
{'strip_env_vars.yml': '''
- name: sensitive environment variables should be stripped from events
  connection: local
  hosts: all
  tasks:
    - shell: echo "Hello, World!"
'''},  # noqa
])
def test_callback_plugin_strips_task_environ_variables(executor, cache, playbook):
    executor.run()
    assert len(cache)
    for event in cache.values():
        assert os.environ['PATH'] not in json.dumps(event)


@pytest.mark.parametrize('playbook', [
{'custom_set_stat.yml': '''
- name: custom set_stat calls should persist to the local disk so awx can save them
  connection: local
  hosts: all
  tasks:
    - set_stats:
        data:
          foo: "bar"
'''},  # noqa
])
def test_callback_plugin_saves_custom_stats(executor, cache, playbook):
    try:
        private_data_dir = tempfile.mkdtemp()
        with mock.patch.dict(os.environ, {'AWX_PRIVATE_DATA_DIR': private_data_dir}):
            executor.run()
            artifacts_path = os.path.join(private_data_dir, 'artifacts', 'custom')
            with open(artifacts_path, 'r') as f:
                assert json.load(f) == {'foo': 'bar'}
    finally:
        shutil.rmtree(os.path.join(private_data_dir))


@pytest.mark.parametrize('playbook', [
{'handle_playbook_on_notify.yml': '''
- name: handle playbook_on_notify events properly
  connection: local
  hosts: all
  handlers:
    - name: my_handler
      debug: msg="My Handler"
  tasks:
    - debug: msg="My Task"
      changed_when: true
      notify:
        - my_handler
'''},  # noqa
])
@pytest.mark.skipif(ANSIBLE_VERSION < '2.5', reason="v2_playbook_on_notify doesn't work before ansible 2.5")
def test_callback_plugin_records_notify_events(executor, cache, playbook):
    executor.run()
    assert len(cache)
    notify_events = [x[1] for x in cache.items() if x[1]['event'] == 'playbook_on_notify']
    assert len(notify_events) == 1
    assert notify_events[0]['event_data']['handler'] == 'my_handler'
    assert notify_events[0]['event_data']['host'] == 'localhost'
    assert notify_events[0]['event_data']['task'] == 'debug'


@pytest.mark.parametrize('playbook', [
{'no_log_module_with_var.yml': '''
- name: ensure that module-level secrets are redacted
  connection: local
  hosts: all
  vars:
    - pw: SENSITIVE
  tasks:
    - uri:
        url: https://example.org
        user: john-jacob-jingleheimer-schmidt
        password: "{{ pw }}"
'''},  # noqa
])
def test_module_level_no_log(executor, cache, playbook):
    # https://github.com/ansible/tower/issues/1101
    # It's possible for `no_log=True` to be defined at the _module_ level,
    # e.g., for the URI module password parameter
    # This test ensures that we properly redact those
    executor.run()
    assert len(cache)
    assert 'john-jacob-jingleheimer-schmidt' in json.dumps(cache.items())
    assert 'SENSITIVE' not in json.dumps(cache.items())
