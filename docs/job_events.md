## Ansible Callback and Job Events

There is no concept of a job event in Ansible. Job Events are JSON structures, created when Ansible calls the Tower callback plugin hooks (*i.e.*, `v2_playbook_on_task_start`, `v2_runner_on_ok`, etc.). The Job Event data structures contain data from the parameters of the callback hooks plus unique IDs that reference other Job Events. There is usually a one-to-one relationship between a Job Event and an Ansible callback plugin function call.


## Job Event Relationships

The Job Event relationship is strictly hierarchical. In the example details below, each Job Event bullet is related to the previous Job Event to form a hierarchy:

* There is always one and only one `v2_playbook_on_start` event and it is the first event.
* `v2_playbook_on_play_start` is generated once per-play in the playbook; two such events would be generated from the playbook example below.
* The `v2_playbook_on_task_start` function is called once for each task under the default execution strategy. Other execution strategies (*i.e.*, free or serial) can result in the `v2_playbook_on_task_start` function being called multiple times, one for each host. Tower only creates a Job Event for the **first** `v2_playbook_on_task_start` call. Subsequent calls for the same task do **not** result in Job Events being created.
* `v2_runner_on_[ok, failed, skipped, unreachable, retry, item_on_ok, item_on_failed, item_on_skipped]`; one `v2_runner_on_...` Job Event will be created for each `v2_playbook_on_task_start` event.


## Example

Below is an example inventory and playbook outline, along with the Job Events generated and their hierarchical relationship:

```
# inventory
[tower]
hostA
hostB

[postgres]
hostC
```

```
# main.yml
---
- hosts: all
  name: preflight
  tasks:
    - name: check_space_requirements
      ...
    - name: check_ram
      ...
    - name: check_umask
      ...

- hosts: all
  name: install
  tasks:
    - name: install_tower
      ...
      when: inventory_hostname in ['A', 'B']
    - name: install_postgres
      ...
      when: inventory_hostname == 'C'
```

Below is a visualization of how Job Events are related to form a hierarchy given a run of the playbook above:

```
`-- playbook_on_start
    |-- playbook_on_play_start-preflight
    |   |-- playbook_on_task_start-check_space_requirements
    |   |   |-- runner_on_ok_hostA
    |   |   |-- runner_on_ok_hostB
    |   |   `-- runner_on_ok_hostC
    |   |-- playbook_on_task_start-check_ram
    |   |   |-- runner_on_ok_hostA
    |   |   |-- runner_on_ok_hostB
    |   |   `-- runner_on_ok_hostC
    |   `-- playbook_on_task_start-check_umask
    |       |-- runner_on_ok_hostA
    |       |-- runner_on_ok_hostB
    |       `-- runner_on_ok_hostC
    `-- playbook_on_play_start-install
        |-- playbook_on_task_start-install_tower
        |   |-- runner_on_ok_hostA
        |   `-- runner_on_ok_hostB
        `-- playbook_on_task_start-install_postgres
            `-- runner_on_ok_hostC
```


## Job Event Creation Patterns

The Ansible execution strategy heavily influences the creation order of Job Events. The above examples of Job Events creation and hierarchy are also the order in which they are created when the Ansible default execution strategy is used. When other strategies like `free` and `serial` are used, the order in which Job Events are created is slightly different.

Let's take the previous example playbook and Job Events and show the order in which the Job Events may be created when the free strategy is used. Notice how `runner_on_*` Job Events can be created **after** a `playbook_on_task_start` for the next task runs. This is not the case for the default Ansible execution strategy. Under the default Ansible execution strategy, all `runner_on_*` Job Events will be created before the next `playbook_on_task_start` is generated:

```
playbook_on_start
playbook_on_play_start-preflight
  playbook_on_task_start-check_space_requirements
    runner_on_ok_hostA (check_space_requirements)
  playbook_on_task_start-check_ram
    runner_on_ok_hostA (check_ram)
    runner_on_ok_hostC (check_space_requirements)
    runner_on_ok_hostC (check_ram)
  playbook_on_task_start-check_umask
    runner_on_ok_hostB (check_ram)
    runner_on_ok_hostC (check_umask)
    runner_on_ok_hostA (check_umask)
    runner_on_ok_hostB (check_space_requirements)
    runner_on_ok_hostB (check_umask)
playbook_on_play_start-install
  playbook_on_task_start-install_tower
    runner_on_ok_hostB (install_tower)
  playbook_on_task_start-install_postgres
    runner_on_ok_hostC (install_postgres)
    runner_on_ok_hostA (install_tower)
```


## Testing

A management command for event replay exists for replaying jobs at varying speeds and other parameters. Run `awx-manage replay_job_events --help` for additional usage information. To prepare the UI for event replay, load the page for a finished job and then append `_debug` as a parameter to the url.


## Code References

* For a more comprehensive list of Job Events and the hierarchy they form, go here: https://github.com/ansible/awx/blob/devel/awx/main/models/jobs.py#L870
* Exhaustive list of Job Events in Tower: https://github.com/ansible/awx/blob/devel/awx/main/models/jobs.py#L900
