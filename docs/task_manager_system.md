# Task Manager System Overview

The task management system is made up of three separate components:
1. Dependency Manager
2. Task Manager
3. Workflow Manager

Each of these run in a separate dispatched task and can run at the same time as one another.

This system is responsible for deciding when tasks should be scheduled to run. When choosing a task to run, the considerations are:
1. Creation time
2. Job dependencies
3. Capacity

Independent tasks are run in order of creation time, earliest first. Tasks with dependencies are also run in creation time order within the group of task dependencies. Capacity is the final consideration when deciding to release a task to be run by the dispatcher.


## Dependency Manager

Responsible for looking at each pending task and determining whether it should create a dependency for that task.
For example, if `update_on_launch` is enabled of a task, a project update will be created as a dependency of that task. The Dependency Manager is responsible for creating that project update.

Dependencies can also have their own dependencies, for example,

```
+-----------+
|           |                          created by web API call
|   Job A   |
|           |
+-----------+---+
                |
                |
        +-------v----+
        |  Inventory |                 dependency of Job A
        |  Source    |                 created by Dependency Manager
        |  Update B  |
        +------------+-------+
                             |
                             |
                      +------v------+
                      |   Project   |  dependency of Inventory Source Update B
                      |   Update C  |  created by Dependency Manager
                      +-------------+
```


### Dependency Manager Steps

1. Get pending tasks (parent tasks) that have `dependencies_processed = False`
2. Create project update if
    a. not already created
    b. last project update outside of cache timeout window
3. Create inventory source update if
    a. not already created
    b. last inventory source update outside of cache timeout window
4. Check and create dependencies for these newly created dependencies
    a. inventory source updates can have a project update dependency
5. All dependencies are linked to the parent task via the `dependent_jobs` field
    a. This allows us to cancel the parent task if the dependency fails or is canceled
6. Update the parent tasks with `dependencies_processed = True`


## Task Manager

Responsible for looking at each pending task and determining whether Task Manager can start that task.

### Task Manager Steps

1. Get pending, waiting, and running tasks that have `dependencies_processed = True`
2. Before processing pending tasks, the task manager first processes running tasks. This allows it to build a dependency graph and account for the currently consumed capacity in the system.
    a. dependency graph is just an internal data structure that tracks which jobs are currently running. It also handles "soft" blocking logic
    b. the capacity is tracked in memory on the `TaskManagerInstances` and `TaskManagerInstanceGroups` objects which are in-memory representations of the instances and instance groups. These data structures are used to help track what consumed capacity will be as we decide that we will start new tasks, and until such time that we actually commit the state changes to the database.
3. For each pending task:
    a. Check if total number of tasks started on this task manager cycle is > `start_task_limit`
    b. Check if [timed out](#timing-out)
    c. Check if task is blocked
    d. Check if preferred instances have enough capacity to run the task
4. Start the task by changing status to `waiting` and submitting task to dispatcher


## Workflow Manager

Responsible for looking at each workflow job and determining if next node can run

### Workflow Manager Steps

1. Get all running workflow jobs
2. Build up a workflow DAG for each workflow job
3. For each workflow job:
    a. Check if [timed out](#timing-out)
    b. Check if next node can start based on previous node status and the associated success / failure / always logic
4. Create new task and signal start


## Task Manager System Architecture

Each of the three managers has a single entry point, `schedule()`. The `schedule()` function tries to acquire a single, global lock recorded in the database. If the lock cannot be acquired, the method returns. The failure to acquire the lock indicates that there is another instance currently running `schedule()`.

Each manager runs inside an atomic DB transaction. If the dispatcher task that is running the manager is killed, none of the created tasks or updates will take effect.

### Hybrid Scheduler: Periodic + Event

Each manager's `schedule()` function is run (a) periodically by a background task and (b) on job creation or completion. The task manager system would behave correctly if it ran, exclusively, via (a) or (b).

Special note -- the workflow manager is not scheduled to run periodically *directly*, but piggy-backs off the task manager. That is, if task manager sees at least one running workflow job, it will schedule the workflow manager to run.

`schedule()` is triggered via both mechanisms because of the following properties:
1. It reduces the time from launch to running, resulting a better user experience.
2. It is a fail-safe in case we miss code-paths, in the present and future, that change the scheduling considerations for which we should call `schedule()` (_i.e._, adding new nodes to AWX changes the capacity, obscure job error handling that fails a job).

Empirically, the periodic task manager has been effective in the past and will continue to be relied upon with the added event-triggered `schedule()`.

### Bulk Reschedule 

Typically, each manager runs asynchronously via the dispatcher system. Dispatcher tasks take resources, so it is important to not schedule tasks unnecessarily. We also need a mechanism to run the manager *after* an atomic transaction block.

Scheduling the managers are facilitated through the `ScheduleTaskManager`, `ScheduleDependencyManager`, and `ScheduleWorkflowManager` classes. These are utilities that help prevent too many managers from being started via the dispatcher system. Think of it as a "do once" mechanism.

```python3
with transaction.atomic()
  for t in tasks:
    if condition:
      ScheduleTaskManager.schedule()
```

In the above code, we only want to schedule the TaskManager once after all `tasks` have been processed. `ScheduleTaskManager.schedule()` will handle that logic correctly.

### Timing out

Because of the global lock of the manager, only one manager can run at a time. If that manager gets stuck for whatever reason, it is important to kill it and let a new one take its place. As such, there is special code in the parent dispatcher process to SIGKILL any of the task system managers after a few minutes.

There is an important side effect to this. Because the manager `schedule()` runs in a transaction, the next run will have re-process the same tasks again. This could lead a manager never being able to progress from one run to the next, as each time it times out. In this situation the task system is effectively stuck as new tasks cannot start. To mitigate this, each manager will check if it is about to hit the time out period and bail out early if so. This gives the manager enough time to commit the DB transaction, and the next manager cycle will be able to start with the next set of unprocessed tasks. This ensures that the system can still make incremental progress under high workloads (i.e. many pending tasks).


### Job Lifecycle

| Job Status |                                                       State                                                      |
|:-----------|:-------------------------------------------------------------------------------------------------------------------|
| pending    | Job has been launched.  <br>1. Hasn't yet been seen by the scheduler <br>2. Is blocked by another task <br>3. Not enough capacity |
| waiting    | Job submitted to dispatcher via pg_notify
| running    | Job is running on a AWX node.
| successful | Job finished with `ansible-playbook` return code 0.                                                                  |
| failed     | Job finished with `ansible-playbook` return code other than 0.                                                       |
| error      | System failure.                                                                                                    |


### Node Affinity Decider

The Task Manager decides which exact node a job will run on. It does so by considering user-configured group execution policy and user-configured capacity. First, the set of groups on which a job _can_ run on is constructed (see the AWX document on [Clustering](./clustering.md)). The groups are traversed until a node within that group is found. The node with the largest remaining capacity (after accounting for the job's task impact) is chosen first. If there are no instances that can fit the job, then the largest *idle* node is chosen, regardless whether the job fits within its capacity limits. In this second case, it is possible for the instance to exceed its capacity in order to run the job.


## Managers are short-lived

Manager instances are short lived. Each time it runs, a new instance of the manager class is created, relevant data is pulled in from database, and the manager processes the data. After running, the instance is cleaned up.


### Blocking Logic

The blocking logic is handled by a mixture of ORM instance references and task manager local tracking data in the scheduler instance.

There is a distinction between so-called "hard" vs "soft" blocking.

**Hard blocking** refers to dependencies that are represented in the database via the task `dependent_jobs` field. That is, Job A will not run if any of its `dependent_jobs` are still running.

**Soft blocking** refers to blocking logic that doesn't have a database representation. Imagine Job A and B are both based on the same job template, and concurrent jobs is `disabled`. Job B will be blocked from running if Job A is already running. This is determined purely by the task manager tracking running jobs via the Dependency Graph.


### Task Manager Rules

* Groups of blocked tasks run in chronological order
* Tasks that are not blocked run whenever there is capacity available in the instance group that they are set to run in (one job is always allowed to run per instance group, even if there isn't enough capacity)
* Only one Project Update for a Project may be running at a time
* Only one Inventory Update for an Inventory Source may be running at a time
* Only one Job for a Job Template may be running at a time (the `allow_simultaneous` feature relaxes this condition)
* Only one System Job may be running at a time


### Update on Launch Logic

This is a feature in AWX where dynamic inventory and projects associated with Job Templates may be set to invoke and update when related Job Templates are launched. Related to this feature is a cache feature on dynamic inventory updates and project updates. The rules for these two intertwined features are below:

* Projects marked as `update on launch` should trigger a project update when a related job template is launched.
* Inventory sources marked as `update on launch` should trigger an inventory update when a related job template is launched.
* Spawning of project updates and/or inventory updates should **not** be triggered when a related job template is launched **IF** there is an update && the last update finished successfully && the finished time puts the update within the configured cache window.
* **Note:** `update on launch` spawned jobs (_i.e._, InventoryUpdate and ProjectUpdate) are considered dependent jobs; in other words, the `launch_type` is `dependent`. If a `dependent` job fails, then everything related to it should also fail.

For example permutations of blocking, take a look at this [Task Manager Dependency Rules and Permutations](https://docs.google.com/a/redhat.com/document/d/1AOvKiTMSV0A2RHykHW66BZKBuaJ_l0SJ-VbMwvu-5Gk/edit?usp=sharing) doc.
