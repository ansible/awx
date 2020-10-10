# Task Manager Overview

The task manager is responsible for deciding when jobs should be scheduled to run. When choosing a task to run, the considerations are:
1. Creation time
2. Job dependencies
3. Capacity

Independent jobs are run in order of creation time, earliest first. Jobs with dependencies are also run in creation time order within the group of job dependencies. Capacity is the final consideration when deciding to release a job to be run by the task dispatcher.

## Task Manager Architecture

The task manager has a single entry point, `Scheduler().schedule()`. The method may be called in parallel, at any time, as many times as the user wants. The `schedule()` function tries to acquire a single, global lock using the Instance table first recorded in the database. If the lock cannot be acquired, the method returns. The failure to acquire the lock indicates that there is another instance currently running `schedule()`.

### Hybrid Scheduler: Periodic + Event
The `schedule()` function is run (a) periodically by a background task and (b) on job creation or completion. The task manager system would behave correctly if it ran, exclusively, via (a) or (b).

`schedule()` is triggered via both mechanisms because of the following properties:
1. It reduces the time from launch to running, resulting a better user experience.
2. It is a fail-safe in case we miss code-paths, in the present and future, that change the scheduling considerations for which we should call `schedule()` (_i.e._, adding new nodes to Tower changes the capacity, obscure job error handling that fails a job).

Empirically, the periodic task manager has been effective in the past and will continue to be relied upon with the added event-triggered `schedule()`.

### Scheduler Algorithm

 * Get all non-completed jobs, `all_tasks`
 * Detect finished workflow jobs
 * Spawn next workflow jobs if needed
 * For each pending job, start with the oldest created job
   * If the job is not blocked, and there is capacity in the instance group queue, then mark it as `waiting` and submit the job.


### Job Lifecycle

| Job Status |                                                       State                                                      |
|:----------:|:------------------------------------------------------------------------------------------------------------------:|
| pending    | Job has been launched.  <br>1. Hasn't yet been seen by the scheduler <br>2. Is blocked by another task <br>3. Not enough capacity |
| waiting    | Job published to an AMQP queue.
| running    | Job is running on a Tower node.
| successful | Job finished with `ansible-playbook` return code 0.                                                                  |
| failed     | Job finished with `ansible-playbook` return code other than 0.                                                       |
| error      | System failure.                                                                                                    |


### Node Affinity Decider

The Task Manager decides which exact node a job will run on. It does so by considering user-configured group execution policy and user-configured capacity. First, the set of groups on which a job _can_ run on is constructed (see the AWX document on [Clustering](https://github.com/ansible/awx/blob/devel/docs/clustering.md)). The groups are traversed until a node within that group is found. The node with the largest remaining capacity that is idle is chosen first. If there are no idle nodes, then the node with the largest remaining capacity greater than or equal to the job capacity requirements is chosen.


## Code Composition

The main goal of the new task manager is to run in our HA environment. This translates to making the task manager logic run on any Tower node. To support this, we need to remove any reliance on the state between task manager schedule logic runs. A future goal of AWX is to design the task manager to have limited/no access to the database for this feature. This secondary requirement, combined with performance needs, led to the creation of partial models that wrap dict database model data.


### Blocking Logic

The blocking logic is handled by a mixture of ORM instance references and task manager local tracking data in the scheduler instance.


## Acceptance Tests

The new task manager should, in essence, work like the old one. Old task manager features were identified while new ones were discovered in the process of creating the new task manager. Rules for the new task manager behavior are iterated below; testing should ensure that those rules are followed.


### Task Manager Rules

* Groups of blocked tasks run in chronological order
* Tasks that are not blocked run whenever there is capacity available in the instance group that they are set to run in (one job is always allowed to run per instance group, even if there isn't enough capacity)
* Only one Project Update for a Project may be running at a time
* Only one Inventory Update for an Inventory Source may be running at a time
* Only one Job for a Job Template may be running at a time (the `allow_simultaneous` feature relaxes this condition)
* Only one System Job may be running at a time


### Update on Launch Logic

This is a feature in Tower where dynamic inventory and projects associated with Job Templates may be set to invoke and update when related Job Templates are launched. Related to this feature is a cache feature on dynamic inventory updates and project updates. The rules for these two intertwined features are below:

* Projects marked as `update on launch` should trigger a project update when a related job template is launched.
* Inventory sources marked as `update on launch` should trigger an inventory update when a related job template is launched.
* Spawning of project updates and/or inventory updates should **not** be triggered when a related job template is launched **IF** there is an update && the last update finished successfully && the finished time puts the update within the configured cache window.
* **Note:** `update on launch` spawned jobs (_i.e._, InventoryUpdate and ProjectUpdate) are considered dependent jobs; in other words, the `launch_type` is `dependent`. If a `dependent` job fails, then everything related to it should also fail.

For example permutations of blocking, take a look at this [Task Manager Dependency Dependency Rules and Permutations](https://docs.google.com/a/redhat.com/document/d/1AOvKiTMSV0A2RHykHW66BZKBuaJ_l0SJ-VbMwvu-5Gk/edit?usp=sharing) doc.
