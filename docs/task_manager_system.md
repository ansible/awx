# Task Manager Overview

The task manager is responsible for deciding when jobs should be introduced to celery for running. When choosing a task to run the considerations are: (1) creation time, (2) job dependency, (3) capacity.

Independent jobs are ran in order of creation time, earliest first. Jobs with dependencies are also ran in creation time order within the group of job dependencies. Capacity is the final consideration when deciding to release a job to be ran by celery.

## Task Manager Architecture

The task manager has a single entry point, `Scheduler().schedule()`. The method may be called in parallel, at any time, as many times as the user wants. The `schedule()` function tries to aquire a single, global, lock using the Instance table first record in the database. If the lock can not be aquired the method returns. The failure to aquire the lock indicates that there is another instance currently running `schedule()`.

### Hybrid Scheduler: Periodic + Event 
The `schedule()` function is ran (a) periodically by a celery task and (b) on job creation or completion. The task manager system would behave correctly if ran, exclusively, via (a) or (b). We chose to trigger `schedule()` via both mechanisms because of the nice properties I will now mention. (b) reduces the time from launch to running, resulting a better user experience. (a) is a fail-safe in case we miss code-paths, in the present and future, that change the 3 scheduling considerations for which we should call `schedule()` (i.e. adding new nodes to tower changes the capacity, obscure job error handling that fails a job)
 Emperically, the periodic task manager has served us well in the past and we will continue to rely on it with the added event-triggered `schedule()`.
 
 ### Scheduler Algorithm
 * Get all non-completed jobs, `all_tasks`
 * Generate the hash tables from `all_tasks`:
   * `<job_template_id, True/False>` indicates a job is running
   * `<project_id, True/False>` indicates a project update is running
   * `<inventory_id, True/False>` indicates a job template or inventory update is running
   * `<inventory_source_id, True/False>` indiciates an inventory update is running
   * `<workflow_job_template_id, True/False>` indiciates a workflow job is running
   * `<project_id, latest_project_update_partial>` used to determine cache timeout
   * `<inventory_id, [ inventory_source_partial, ... ]>`  used to determine cache timeout and dependencies to spawn
   * `<inventory_source_id, latest_inventory_update_partial>` used to determine cache timeout
 * Detect finished workflow jobs
 * Spawn next workflow jobs if needed
 * For each pending jobs; start with oldest created job and stop when no capacity == 0
   * If job is not blocked, determined using generated hash tables, and there is capacity, then mark the as `waiting` and submit the job to celery.
 
### Job Lifecycle
| Job Status |                                                       State                                                      |
|:----------:|:------------------------------------------------------------------------------------------------------------------:|
| pending    | Job launched.  <br>1. Hasn't yet been seen by the scheduler <br>2. Is blocked by another task <br>3. Not enough capacity |
| waiting    | Job submitted to celery.                                                                                           |
| running    | Job running in celery.                                                                                             |
| successful | Job finished with ansible-playbook return code 0.                                                                  |
| failed     | Job finished with ansible-playbook return code other than 0.                                                       |
| error      | System failure.                                                                                                    |

## Code Composition
The main goal of the new task manager is to run in our HA environment. This translates to making the task manager logic run on any tower node. To support this we need to remove any reliance on state between task manager schedule logic runs. We had a secondary goal in mind of designing the task manager to have limited/no access to the database for the future federation feature. This secondary requirement combined with performance needs led us to create partial models that wrap dict database model data.

### Partials
Partials wrap a subset of Django model dict data, provide a simple static query method that is purpose built to support the populating of the task manager hash tables,  have a link back to the model which they are wrapping so that the original Django ORM model for which the partial is wrapping can be easily gotten, and can be made serializable via `<type, self.data>` since `self.data` is a `dict` of the database record. 

### Blocking Logic
The blocking logic has been moved from the respective ORM model to the code that manages the dependency hash tables. The blocking logic could easily be moved to the partials or evne the ORM models. However, the per-model blocking logic code would be operating on the dependency hash tables; not on ORM models as in the previous design. The blocking logic is kept close to the data-structures required to operate on. 

## Acceptance Tests

The new task manager should, basically, work like the old one. Old task manager features were identified and new ones discovered in the process of creating the new task manager. Rules for the new task manager behavior are iterated below. Testing should ensure that those rules are followed.

### Task Manager Rules
* Groups of blocked tasks run in chronological order
* Tasks that are not blocked run whenever there is capacity available
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

Example permutations of blocking: https://docs.google.com/a/redhat.com/document/d/1AOvKiTMSV0A2RHykHW66BZKBuaJ_l0SJ-VbMwvu-5Gk/edit?usp=sharing
