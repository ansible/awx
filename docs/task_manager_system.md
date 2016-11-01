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

## todo
 
## Code Composition
* partials
* 

## Acceptance Tests
* assemelate with .md and trim the fat https://docs.google.com/a/redhat.com/document/d/1AOvKiTMSV0A2RHykHW66BZKBuaJ_l0SJ-VbMwvu-5Gk/edit?usp=sharing









