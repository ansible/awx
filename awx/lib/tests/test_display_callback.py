from collections import OrderedDict
import json
import mock
import os
import sys

import pytest

# ansible uses `ANSIBLE_CALLBACK_PLUGINS` and `ANSIBLE_STDOUT_CALLBACK` to
# discover callback plugins;  `ANSIBLE_CALLBACK_PLUGINS` is a list of paths to
# search for a plugin implementation (which should be named `CallbackModule`)
#
# this code modifies the Python path to make our
# `awx.lib.tower_display_callback` callback importable (because `awx.lib`
# itself is not a package)
#
# we use the `tower_display_callback` imports below within this file, but
# Ansible also uses them when it discovers this file in
# `ANSIBLE_CALLBACK_PLUGINS`
CALLBACK = os.path.splitext(os.path.basename(__file__))[0]
PLUGINS = os.path.dirname(__file__)
with mock.patch.dict(os.environ, {'ANSIBLE_STDOUT_CALLBACK': CALLBACK,
                                  'ANSIBLE_CALLBACK_PLUGINS': PLUGINS}):
    from ansible.cli.playbook import PlaybookCLI
    from ansible.executor.playbook_executor import PlaybookExecutor
    from ansible.inventory import Inventory
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars import VariableManager

    # Add awx/lib to sys.path so we can use the plugin
    path = os.path.abspath(os.path.join(PLUGINS, '..', '..'))
    if path not in sys.path:
        sys.path.insert(0, path)

    from tower_display_callback import TowerDefaultCallbackModule as CallbackModule  # noqa
    from tower_display_callback.events import event_context  # noqa


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
    options = cli.parser.parse_args([])[0]
    loader = DataLoader()
    variable_manager = VariableManager()
    inventory = Inventory(loader=loader, variable_manager=variable_manager,
                          host_list=['localhost'])
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
'''}  # noqa
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
'''},  # noqa
])
def test_callback_plugin_no_log_filters(executor, cache, playbook):
    executor.run()
    assert len(cache)
    assert 'SENSITIVE' not in json.dumps(cache.items())


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
