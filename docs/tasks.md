Background Tasks in AWX
=======================

AWX runs a lot of Python code asynchronously _in the background_ - meaning
_outside_ of the context of an HTTP request, such as:

* Any time a Job is launched in AWX (a Job Template, an Adhoc Command, a Project
  Update, an Inventory Update, a System Job), a background process retrieves
  metadata _about_ that job from the database and forks some process (e.g.,
  `ansible-playbook`, `awx-manage inventory_import`) 
* Certain expensive or time consuming tasks run in the background
  asynchronously (like deleting an inventory).
* AWX runs a variety of periodic background tasks on a schedule.  Some examples
  are:
    - AWX's "Task Manager/Scheduler" wakes up periodically and looks for
      `pending` jobs that have been launched and are ready to start running.
    - AWX periodically runs code that looks for scheduled jobs and launches
      them.
    - AWX runs a variety of periodic tasks that clean up temporary files, and
      perform various administrative checks
    - Every node in an AWX cluster runs a periodic task that serves as
      a heartbeat and capacity check

Tasks, Queues and Workers
----------------

To accomplish this, AWX makes use of a "Task Queue" abstraction.  Task Queues
are used as a mechanism to distribute work across machines in an AWX
installation.  A Task Queue's input is a unit of work called a Task. Dedicated
worker processes running on every AWX node constantly monitor these queues for
new work to perform.

AWX communicates with these worker processes via AMQP - using RabbitMQ,
specifically - to mediate between clients and workers. To initiate a task, the
client (generally, Python code in the AWX API) publishes a message to a queue,
and RabbitMQ then delivers that message to one or more workers.

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

Heartbeats, Capacity, and Job Reaping
------------------------------------
One of the most important tasks in a clustered AWX installation is the periodic
heartbeat task.  This task runs periodically on _every_ node, and is used to
record a heartbeat and system capacity for that node (which is used by the
scheduler when determining where to placed launched jobs).

If a node in an AWX cluster discovers that one of its peers has not updated its
heartbeat within a certain grace period, it is assumed to be offline, and its
capacity is set to zero to avoid scheduling new tasks on that node.
Additionally, jobs allegedly running or scheduled to run on that node are
assumed to be lost, and "reaped", or marked as failed.

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
