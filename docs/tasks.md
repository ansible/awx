Background Tasks in AWX
=======================

In this document, we will go into a bit of detail about how and when AWX runs Python code _in the background_ (_i.e._, **outside** of the context of an HTTP request), such as:

* Any time a Job is launched in AWX (a Job Template, an Ad Hoc Command, a Project
  Update, an Inventory Update, a System Job), a background process retrieves
  metadata _about_ that job from the database and forks some process (_e.g._,
  `ansible-playbook`, `awx-manage inventory_import`)
* Certain expensive or time-consuming tasks running in the background
  asynchronously (_e.g._, when deleting an inventory).
* AWX runs a variety of periodic background tasks on a schedule.  Some examples
  are:
    - AWX's "Task Manager/Scheduler" wakes up periodically and looks for
      `pending` jobs that have been launched and are ready to start running
    - AWX periodically runs code that looks for scheduled jobs and launches
      them
    - AWX runs a variety of periodic tasks that clean up temporary files, and
      performs various administrative checks
    - Every node in an AWX cluster runs a periodic task that serves as
      a heartbeat and capacity check


Tasks, Queues and Workers
----------------

To accomplish this, AWX makes use of a "Task Queue" abstraction.  Task Queues are used as a mechanism to distribute work across machines in an AWX installation.  A Task Queue's input is a unit of work called a Task. Dedicated worker processes running on every AWX node constantly monitor these queues for new work to perform.

AWX communicates with these worker processes to mediate between clients and workers. This is done via distributed queues and the already-acknowledged local queue that the Dispatcher is working through. Simply put: to initiate a task, the client (generally, Python code in the AWX API) publishes a message to a queue, which is then delivered to one or more workers.

Clustered AWX installations consist of multiple workers spread across every
node, giving way to high availability and horizontal scaling.


Direct vs Fanout Messages
-------------------------

AWX publishes tasks in two distinct ways.

*Direct* messages are bound _directly_ to a specific named queue.  When you launch
a Job Template in AWX, it looks at the available capacity of the various nodes
in your cluster and chooses an `Execution Node` where the playbook will run.
In this scenario, AWX publishes a message to a direct queue associated with
that AWX node.  The dispatcher process running on that AWX node is specifically
bound to _listen_ for new events on their instance-specific queue.

Certain direct queues in AWX are bound to by _every_ AWX node.  For example,
when an inventory deletion task is published, any available node across the
entire AWX may perform the work.  Under _direct_ exchanges, every published
message is consumed and handled by *one* worker process.

*Fanout* messages are sent out in a broadcast fashion.  When you change
a setting value in the AWX API, a fanout message is broadcast to _every_ AWX
node in your cluster, and code runs on _every_ node.


Defining and Running Tasks
--------------------------

Tasks are defined in AWX's source code, and generally live in the
`awx.main.tasks` module.  Tasks can be defined as simple functions:

    from awx.main.dispatch.publish import task

    @task()
    def add(a, b):
        return a + b

...or classes that define a `run` method:

    @task()
    class Adder:
        def run(self, a, b):
            return a + b

To publish a task and run it in the background, use the `apply_async()`
function:

    add.apply_async([1, 1])
    Adder.apply_async([1, 1])

When you run this function, a JSON message is composed and published to the
appropriate AMQP queue:

    {
        "uuid": "<some_unique_string>",
        "args": [1, 1],
        "kwargs": {},
        "task": "awx.main.tasks.add"
    }

When a background worker receives the message, it deserializes it and runs the
associated Python code:

    awx.main.tasks.add(123)


Dispatcher Implementation
-------------------------
Every node in an AWX install runs `awx-manage run_dispatcher`, a Python process
that uses the `kombu` library to consume messages from the appropriate queues
for that node (the default shared queue, a queue specific to the node's
hostname, and the broadcast queue).  The Dispatcher process manages a pool of
child processes that it distributes inbound messages to.  These worker
processes perform the actual work of deserializing published tasks and running
the associated Python code.


Debugging
---------
`awx-manage run_dispatcher` includes a few flags that allow interaction and
debugging:

```
[root@awx /]# awx-manage run_dispatcher --status
2018-09-14 18:39:22,223 WARNING  awx.main.dispatch checking dispatcher status for awx
awx[pid:9610] workers total=4 min=4 max=60
.  worker[pid:9758] sent=12 finished=12 qsize=0 rss=106.730MB [IDLE]
.  worker[pid:9769] sent=5 finished=5 qsize=0 rss=105.141MB [IDLE]
.  worker[pid:9782] sent=5 finished=4 qsize=1 rss=110.430MB
     - running 0c1deb4d-25ae-49a9-804f-a8afd05aff29 RunJob(*[9])
.  worker[pid:9787] sent=3 finished=3 qsize=0 rss=101.824MB [IDLE]
```

This outputs running and queued task UUIDs handled by a specific dispatcher
(which corresponds to `main_unifiedjob.celery_task_id` in the database):

```
[root@awx /]# awx-manage run_dispatcher --running
2018-09-14 18:39:22,223 WARNING  awx.main.dispatch checking dispatcher running for awx
['eb3b0a83-86da-413d-902a-16d7530a6b25', 'f447266a-23da-42b4-8025-fe379d2db96f']
```

Additionally, you can tell the local running dispatcher to recycle all of the
workers in its pool.  It will wait for any running jobs to finish and exit when
work has completed, spinning up replacement workers.

```
awx-manage run_dispatcher --reload
```

* * *

In the following sections, we will go further into the details regarding AWX tasks.  They are all decorated by `@task()` in [awx/awx/main/tasks.py](https://github.com/ansible/awx/blob/devel/awx/main/tasks.py)

## Housekeeping Tasks

Task execution in AWX is based on a sophisticated system for scheduling jobs that are launched on demand or at scheduled times, primarily via the `run_task_manager` task.

For further information regarding AWX Schedulers or Task Managers, refer to the [Task Manager Overview page](https://github.com/ansible/awx/blob/devel/docs/task_manager_system.md) of the AWX documentation.


### Heartbeats, Capacity, and Job Reaping

One of the most important tasks in a clustered AWX installation is the periodic heartbeat task.  This task runs periodically on _every_ node, and is used to record a heartbeat and system capacity for that node (which is used by the scheduler when determining where to place launched jobs).

If a node in an AWX cluster discovers that one of its peers has not updated its heartbeat within a certain grace period, it is assumed to be offline, and its capacity is set to zero to avoid scheduling new tasks on that node. Additionally, jobs allegedly running or scheduled to run on that node are assumed to be lost, and "reaped", or marked as failed.


#### Isolated Tasks and Their Heartbeats

AWX reports as much status as it can via the browsable API at `/api/v2/ping` in order to provide validation of the health of an instance, including the timestamps of the last heartbeat. Since isolated nodes don't have access to the AWX database, their heartbeats are performed by controller nodes instead. A periodic task, `awx_isolated_heartbeat`, is responsible for periodically connecting from a controller to each isolated node and retrieving its capacity (via SSH).

When a job is scheduled to run on an isolated instance, the controller instance puts together the metadata required to run the job and then transfers it to the isolated instance. Once the metadata has been synchronized to the isolated host, the controller instance starts a process on the isolated instance, which consumes the metadata and starts running `ansible/ansible-playbook`. As the playbook runs, job artifacts (such as `stdout` and job events) are written to disk on the isolated instance.

Alternatively: "While the job runs on the isolated instance, the controller instance periodically checks for and copies the job artifacts (_e.g._, `stdout` and job events) that it produces. It processes these until the job finishes running."

To read more about Isolated Instances, refer to the [Isolated Instance Groups](https://docs.ansible.com/ansible-tower/latest/html/administration/clustering.html#isolated-instance-groups) section of the Clustering page in the Ansible Tower Administration guide.


## AWX Jobs

### Unified Jobs

Much of the code in AWX around `ansible` and `ansible-playbook` invocation and interaction has been removed and put into the project `ansible-runner`. AWX now calls out to `ansible-runner` to invoke `ansible` and `ansible-playbook`.

"Unified Jobs" is the categorical name for _all_ types of jobs (_i.e._, it's the parent class of all job class models). On the simplest level, a process is being forked and AWX is recording its output.  Instance capacity determines which jobs get assigned to any specific instance; thus jobs and ad hoc commands use more capacity if they have a higher forks value.

Below are specific details regarding each type of unified job that can be run in AWX.


#### Run Ad Hoc Command

This task spawns an `ansible` process, which then runs a command using Ansible. The different functions contained within this task do the following:

- Return SSH private key data needed for the ad hoc command (only if stored in the database as `ssh_key_data`).
- Build a dictionary of passwords for the SSH private key, SSH user and sudo/su.
- Build an environment dictionary for Ansible.
- Build a command line argument list for running Ansible, optionally using `ssh-agent` for public/private key authentication.
- Return whether the task should use `bwrap`.

For more information on ad hoc commands, read the [Running Ad Hoc Commands section](https://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#running-ad-hoc-commands) of the Inventories page of the Ansible Tower User Guide.


#### Run Job

This task is a definition and set of parameters for running `ansible-playbook` via a Job Template. It defines metadata about a given playbook run, such as a named identifier, an associated inventory to run against, the project and `.yml` playbook file to run, etc.

For more information, visit the [Jobs page](https://docs.ansible.com/ansible-tower/latest/html/userguide/jobs.html) of the Ansible Tower User Guide.


#### Run Project Update

When a Project Update is run in AWX, an `ansible-playbook` command is composed and spawned in a pseudoterminal on one of the servers/containers that make up the AWX installation. This process runs until completion (or until a configurable timeout), and the return code, `stdout`, and `stderr` of the process are recorded in the AWX database.

This task also includes a helper method to build SCM url and extra vars with parameters needed for authentication, as well as a method for returning search/replace strings to prevent output URLs from showing sensitive passwords.

To read more about this topic, visit the [Projects page](https://docs.ansible.com/ansible-tower/latest/html/userguide/projects.html) of the Ansible Tower User Guide.


#### Run Inventory Update

Inventory data can be entered into AWX manually, but many users perform syncs to import inventory data from a variety of supported external sources (_e.g._, GCE, EC2, etc.) via inventory scripts. The goal of the Run Inventory Update task is to translate the JSON inventory data returned from `ansible-inventory` into `Host`, `Group`, and `Inventory` records in the AWX database.

In older versions of AWX, the `INI` files were not exclusive for either specification via environment variables nor for using the credential injectors. The respective credential for each of these types would lay down authentication information, usually in environment variables. Then, inventory-specific logic laid down an `INI` file that was referenced from an environment variable. Currently, if the inventory plugin is available in the installed Ansible version, a `.yml` file will be used instead of the `INI` inventory config. The way that respective credentials have been injected has mostly remained the same.

Additionally, inventory imports are run through a management command. Inventory in `args` get passed to that command, which results in it not being considered to be an Ansible inventory by Runner even though it is.

To read more about inventories, visit the [Inventories page](https://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html) of the Ansible Tower User Guide. For more detail about Runner, visit the [Ansible Runner Integration Overview](https://github.com/ansible/awx/blob/devel/docs/ansible_runner_integration.md) AWX documentation page.


#### System Jobs

The main distinctive feature of a System Job (as compared to all other Unified Jobs) is that a system job runs management commands, which are given the highest priority for execution hierarchy purposes. They also implement a database lock while running, _i.e._, no other jobs can be run during that time on the same node. Additionally, they have a fixed fork impact of 5 vs 1.

You can read more about [Ansible Tower Capacity Determination and Job Impact](https://docs.ansible.com/ansible-tower/latest/html/userguide/jobs.html#at-capacity-determination-and-job-impact) in the Jobs section of the Ansible Tower User Guide.


### Periodic Background Tasks

Generally speaking, these are the tasks which take up a lot of resources which are best for _not_ running via HTTP request.


#### User-Defined Schedules

While jobs can be launched manually in the AWX interface, it's also possible to configure jobs to run automatically on a schedule (such as daily, or every Monday at 9AM). A special background task, `awx_periodic_scheduler`, runs periodically and determines which jobs are ready to be launched.


#### Update Inventory Computed Fields / Delete Inventory

When making changes to inventories or hosts, there are related attributes that are calculated "under the hood" which require the task to be run for the full scale of the inventory. Because computed fields will aggregate overall stats for all of the hosts in the inventory, this can be quite a resource-consuming task, especially when considering a large number of hosts.

Running the Update Inventory Computed Fields task in the background, in response to changes made by the user via the API, updates the aggregated stats for the inventory; it does this by calculating aggregates for the inventory as a whole. Because of this task, the inventory/group/host details can be made consistent within the AWX environment in a manner that is not resource-intensive.


#### Update Host Smart Inventory Memberships

The `smart_inventories` field in AWX uses a membership lookup table that identifies the set of every Smart Inventory a host is associated with. This particular task generates memberships and is launched whenever certain conditions are met (_e.g._, a new host is added or an existing host is modified).

An important thing to note is that this task is only run if the `AWX_REBUILD_SMART_MEMBERSHIP` is set to `True` (default is `False`).

For more information, visit the [Smart Inventories section](https://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#smart-inventories) of the Tower User Guide's "Inventory" page or the AWX documentation page [Inventory Refresh Overview page](https://github.com/ansible/awx/blob/devel/docs/inventory_refresh.md#inventory-changes) in this repo.


#### Deep Copy Model Object

As previously discussed, there are a number of places where tasks run in the background due to slow processing time or high amounts of memory consumption (_e.g._, in cases where nested code is involved). Since it would be difficult to scale resource-intensive code (which would leave the HTTP connection hanging), this task instead acquires all of the attributes of the original object within the HTTP request, constructs a mapping of related objects, then sends this mapping as a parameter to the task call, which is sent via the messaging system.

When the task starts, it receives those attributes and creates the needed related objects (or creates connections to existing objects). At this point the task will check user permissions; some items may remain unlinked if the user who started the copy does not have permissions to it.

This entire process enables a response of a `202 Accepted`, where instead of waiting for a `200 OK` status, it simply indicates that the job is in progress, freeing up resources for other tasks.


#### Handle Setting Changes

Any time the user changes a setting in AWX (_e.g._, in `api/v2/settings`), data will be added to or altered in a database. Since querying databases directly can be extremely time-consuming, each node in a cluster runs a local `redis-cache` server, none of which are aware of each other. They all potentially have different values contained within, but ultimately need to be consistent. So how can this be accomplished?

"Handle Setting Changes" provides the solution!  This "fanout" task (_i.e._, all nodes execute it) makes it so that there is a single source of truth even within a clustered system. Whenever a database setting is accessed, and that setting's name is not present in `redis-cache`, it grabs the setting from the database and then populates it in the applicable node's cache.  When any database setting gets altered, all of the `redis-cache` servers on each node needs to "forget" the value that they previously retained. By deleting the setting in `redis-cache` on all nodes with the use of this task, we assure that the next time it is accessed, the database will be consulted for the most up-to-date value.


### Analytics and Administrative Tasks

#### Profile SQL

This task allows the user to turn on a global profiler in their system, so that AWX can profile all of the SQL queries that they make.  This is a "fanout" style task (meaning all nodes execute it), and one of the main benefits is that it assists with identifying slow queries.


#### Gather Analytics

The analytics collection `gather()` and `ship()` functions are called by an `awx-manage gather_analytics --ship` command, which runs on whichever instance it is invoked on. When these functions are called by Celery beat (currently at midnight local time), it is run on one `execution_node` by the Python in the AWX virtualenv.

For more details about analytics, please visit the [Usability Analytics and Data Collection](https://docs.ansible.com/ansible-tower/latest/html/administration/usability_data_collection.html) page.


#### Run Administrative Checks

This task checks that the license currently in use is valid and alerts the admin user(s) via email when they are in danger of going over capacity and/or when the license is about to expire. Specifically (in cases of going over capacity), it triggers when the node count is at or over 90% of what the license allows.


#### Purge Old Stdout Files

AWX sometimes buffers `stdout` for playbook runs to disk _when users download stdout for a job run_.  This task implements a periodic cleanup of the directory where this data is stored.


#### Delete Project Files

A "fanout" task (meaning all nodes execute it), this looks at the local file system and deletes project-related files (generally, source control clones) when a Project is deleted from AWX.


#### Handle Work Success/Error

This task is part of the process of running a unified job.  For example, let's say that a Project Update gets started, and it takes 10 seconds; it's done and ready to go with no more dependencies.  Instead of waiting for the scheduler to wake up again (typically every 30 seconds), this task will alert the scheduler to go ahead and run the next phase of the dependency graph.

In case of an error, the same thing happens as above but with a "fail" vs a "success".  So for example if a workflow node is set to run "on fail", the Handle Work task will wake up the scheduler and ensure that the next step runs.  It is also useful in recording cascading errors (_e.g._, if a job has an error, it will look at what it depended on and report status details for all of those dependencies as well).


#### Send Notifications

When a user creates a notification template in `/api/v2/notification_templates`, they can assign it to any of the various objects that support it (_i.e._, Job Templates).  They can also set the appropriate trigger level for when they want the notification task to run (_e.g._, error, success, or any). When the object that the notification was attached to runs and triggers the notification template, it sends a notification, and the action of sending it is recorded in `/api/v2/notifications/`.

Notifications assigned at certain levels will inherit traits defined on parent objects in different ways.  For example, ad hoc commands will use notifications defined on the Organization that the inventory is associated with.

For more details on notifications, visit the [Notifications page](https://docs.ansible.com/ansible-tower/3.4.3/html/userguide/notifications.html) of the Tower user guide, or the AWX documentation on [Notification System Overview](https://github.com/ansible/awx/blob/devel/docs/notification_system.md) in this repository.
