# Task Manager Overview

The task manager is responsible for deciding when jobs should scheduled to run. When choosing a task to run the considerations are: (1) creation time, (2) job dependency, (3) capacity.

Independent jobs are ran in order of creation time, earliest first. Jobs with dependencies are also ran in creation time order within the group of job dependencies. Capacity is the final consideration when deciding to release a job to be ran by the task dispatcher.

## Task Manager Architecture

The task manager has a single entry point, `Scheduler().schedule()`. The method may be called in parallel, at any time, as many times as the user wants. The `schedule()` function tries to aquire a single, global, lock using the Instance table first record in the database. If the lock cannot be aquired the method returns. The failure to aquire the lock indicates that there is another instance currently running `schedule()`.

### Hybrid Scheduler: Periodic + Event 
The `schedule()` function is ran (a) periodically by a background task and (b) on job creation or completion. The task manager system would behave correctly if ran, exclusively, via (a) or (b). We chose to trigger `schedule()` via both mechanisms because of the nice properties I will now mention. (b) reduces the time from launch to running, resulting a better user experience. (a) is a fail-safe in case we miss code-paths, in the present and future, that change the 3 scheduling considerations for which we should call `schedule()` (i.e. adding new nodes to tower changes the capacity, obscure job error handling that fails a job)
 Emperically, the periodic task manager has served us well in the past and we will continue to rely on it with the added event-triggered `schedule()`.
 
### Scheduler Algorithm
 * Get all non-completed jobs, `all_tasks`
 * Detect finished workflow jobs
 * Spawn next workflow jobs if needed
 * For each pending jobs; start with oldest created job
   * If job is not blocked, and there is capacity in the instance group queue, then mark the as `waiting` and submit the job to RabbitMQ.
 
### Job Lifecycle
| Job Status |                                                       State                                                      |
|:----------:|:------------------------------------------------------------------------------------------------------------------:|
| pending    | Job launched.  <br>1. Hasn't yet been seen by the scheduler <br>2. Is blocked by another task <br>3. Not enough capacity |
| waiting    | Job published to an AMQP queue.
| running    | Job running on a Tower node.
| successful | Job finished with ansible-playbook return code 0.                                                                  |
| failed     | Job finished with ansible-playbook return code other than 0.                                                       |
| error      | System failure.                                                                                                    |
### Node Affinity Decider
The Task Manager decides what exact node a job will run on. It does so by considering user-configured (1) group execution policy and (2) capacity. First, the set of groups on which a job _can_ run on is constructed (see clustering.md). The groups are traversed until a node within that group is found. The node with the largest remaining capacity that is idle is chosen first. If there are no idle nodes, then the node with the largest remaining capacity >= the job capacity requirements is chosen.

## Code Composition
The main goal of the new task manager is to run in our HA environment. This translates to making the task manager logic run on any tower node. To support this we need to remove any reliance on state between task manager schedule logic runs. We had a secondary goal in mind of designing the task manager to have limited/no access to the database for the future federation feature. This secondary requirement combined with performance needs led us to create partial models that wrap dict database model data.

### Blocking Logic
The blocking logic is handled by a mixture of ORM instance references and task manager local tracking data in the scheduler instance

## Acceptance Tests

The new task manager should, basically, work like the old one. Old task manager features were identified and new ones discovered in the process of creating the new task manager. Rules for the new task manager behavior are iterated below. Testing should ensure that those rules are followed.

### Task Manager Rules
* Groups of blocked tasks run in chronological order
* Tasks that are not blocked run whenever there is capacity available in the instance group they are set to run in***
 * ***1 job is always allowed to run per instance group, even if there isn't enough capacity.
* Only 1 Project Updates for a Project may be running
* Only 1 Inventory Update for an Inventory Source may be running
* For a related Project, only a Job xor Project Update may be running
* For a related Inventory, only a Job xor Inventory Update(s) may be running
* Only 1 Job for a Job Template may be running**
  * **allow_simultaneous feature relaxes this condition
* Only 1 System Job may be running

### Update on Launch Logic
Feature in Tower where dynamic inventory and projects associated with Job Templates may be set to invoke and update when related Job Templates are launch. Related to this feature is a cache feature on dynamic inventory updates and project updates. The rules for these two intertwined features are below.
* projects marked as update on launch should trigger a project update when a related job template is launched
* inventory sources marked as update on launch should trigger an inventory update when a related job template is launched
* spawning of project update and/or inventory updates should **not** be triggered when a related job template is launched **IF** there is an update && the last update finished successfully && the finished time puts the update within the configured cache window.
* **Note:** Update on launch spawned jobs (i.e. InventoryUpdate and ProjectUpdate) are considered dependent jobs. The `launch_type` is `dependent`. If a `dependent` jobs fails then the dependent job should also fail.

Example permutations of blocking: https://docs.google.com/a/redhat.com/document/d/1AOvKiTMSV0A2RHykHW66BZKBuaJ_l0SJ-VbMwvu-5Gk/edit?usp=sharing
