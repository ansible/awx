# AWX Clustering Overview

AWX supports multi-node configurations. Here is an example configuration with two control plane nodes.

```
       ┌───────────────────────────┐
       │      Load-balancer        │
       │   (configured separately) │
       └───┬───────────────────┬───┘
           │   round robin API │
           ▼       requests    ▼

  AWX Control               AWX Control
    Node 1                    Node 2
┌──────────────┐           ┌──────────────┐
│              │           │              │
│ ┌──────────┐ │           │ ┌──────────┐ │
│ │ awx-task │ │           │ │ awx-task │ │
│ ├──────────┤ │           │ ├──────────┤ │
│ │ awx-ee   │ │           │ │ awx-ee   │ │
│ ├──────────┤ │           │ ├──────────┤ │
│ │ awx-web  │ │           │ │ awx-web  │ │
│ ├──────────┤ │           │ ├──────────┤ │
│ │ redis    │ │           │ │ redis    │ │
│ └──────────┘ │           │ └──────────┘ │
│              │           │              │
└──────────────┴─────┬─────┴──────────────┘
                     │
                     │
               ┌─────▼─────┐
               │ Postgres  │
               │ database  │
               └───────────┘
```

There are two main deployment types, virtual machines (VM) or K8S. Ansible Automation Platform (AAP) can be installed via VM or K8S deployments. The upstream AWX project can only be installed via a K8S deployment. Either deployment type supports cluster scaling.
- Control plane nodes run a number of background services that are managed by supervisord
  - dispatcher
  - wsbroadcast
  - callback receiver
  - receptor (*managed under systemd)
  - redis (*managed under systemd)
  - uwsgi
  - daphne
  - rsyslog
- For K8S deployments, these background processes are containerized
  - `awx-ee`: receptor
  - `awx-web`: uwsgi, daphne, wsbroadcast, rsyslog
  - `awx-task`: dispatcher, callback receiver
  - `redis`: redis
- Each control node is monolithic and contains all the necessary components for handling API requests and running jobs.
- A load balancer in front of the cluster can handle incoming web requests and send them control nodes based on load balancing rules (e.g. round robin)
- All control nodes on the cluster interact single, shared Postgres database
- AWX is configured in such a way that if any of these services or their components fail, then all services are restarted. If these fail sufficiently (often in a short span of time), then the entire instance will be placed offline in an automated fashion in order to allow remediation without causing unexpected behavior.

## Scaling the cluster

For AAP deployments, scaling up involves modifying `inventory`and re-running setup.sh
For K8s deployments, scaling up is handled by changing the number of replicas in the AWX replica set.

After scaling up, the new control plane node is registered in the database as a new `Instance`.

Instance types:
`hybrid` (AAP only) - control plane node that can also run jobs
`control` - control plane node that cannot run jobs
`execution` - not a control node, this instance can only run jobs
`hop` (AAP only) - not a control node, this instance serves to route traffic from control nodes to execution nodes

Note, hybrid (AAP only) and control nodes are identical other than the `type` indicated in the database. `control`-type nodes still have all the machinery to run jobs, but are disabled through the API. The reason is that users may wish to provision control nodes with less hardware resources, and have a separate fleet of nodes to run jobs (i.e. execution nodes).

## Communication between nodes

Each control node is connected to the other nodes via the following

| Node           | Connection Type      | Purpose                            |
|----------------|----------------------|------------------------------------|
| control node   | websockets, receptor | sending websockets, heartbeat      |
| execution      | receptor             | submitting jobs, heartbeat         |
| hop (AAP only) | receptor             | routing traffic to execution nodes |
| postgres       | postgres TCP/IP      | read and write queries, pg notify  |


I.e. control nodes are connected to other control nodes via websockets and receptor.

### Receptor

Receptor provides an overlay network that connects control, execution, and hop nodes together.

Receptor is used for establishing periodic heartbeats and submitting jobs to execution nodes.

The connected nodes form a mesh. It works by connecting nodes via persistent TCP/IP connections. Importantly, once a node is on the mesh, it can be accessed from all other nodes on the mesh, even if not directly connected via TCP.

node A <---TCP---> node B <---TCP---> node C

node A is reachable from node C (and vice versa). Receptor does this by routing traffic through the receptor process running on node B.


### Websockets

Each control node establishes a websocket connection to each other control node. We call this the websocket backplane.

```
┌────────┐
│        │
│browser │
│        │
└───┬────┘
    │ websocket connection
    │
┌───▼─────┐            ┌─────────┐
│ control │            │ control │
│ node A  │◄───────────┤ node B  │
└─────────┘  websocket └─────────┘
             connection
             (job event)
```

The AWX UI will open websocket connections to the server to stream certain data in real time. For example, the job events on the Job Detail Page is streaming over a websocket connection and rendered in real time. The browser has no way of choosing which control node it connects to, instead the connection is handled by the load balancer, the same way http API requests are handled.

Therefore, we could have a situation where the browser is connected control node A, but is requesting job events that are emitted from control node B. As such, control node B will send job events over a separate, persistent websocket connection to control node A. Once control node A has received that message, it can then propagate it to the browser.

One consequence of this is that control node B must *broadcast* this message to all other control nodes, because it doesn't know which node the browser is connected to.

The websocket backplane is handled by the wsbroadcast service that is part of the application startup.


### Postgres

AWX is a Django application and uses the psycopg2 library to establish connections to the Postgres database.
Only control nodes need direct access to the database.

Importantly AWX relies on the Postgres notify system for inter-process communication. The dispatcher system spawns separate processes/threads that run in parallel. For example, it runs the task manager periodically, and the task manager needs to be able to communicate with the main dispatcher thread. It does this via `pg_notify`.

## Node health

Node health is determined by the `cluster_node_heartbeat`. This is a periodic task that runs on each control node.

1. Get a list of instances registered to the database.
2. `inspect_execution_nodes` looks at each execution node
  a. get a DB advisory lock so that only a single control plane node runs this inspection at given time.
  b. set `last_seen` based on Receptor's own heartbeat system
    - Each node on the Receptor mesh sends advertisements out to other nodes. The `Time` field in this payload can be used to set `last_seen`
  c. use `receptorctl status` to gather node information advertised on the Receptor mesh
  d. run `execution_node_health_check`
    - This is an async task submitted to the dispatcher and attempts to run `ansible-runner --worker-info` against that node
    - This command will return important information about the node's hardware resources like CPU cores, total memory, and ansible-runner version
    - This information will be used to calculate capacity for that instance
3. Determine if other nodes are lost based the `last_seen` value determined in step 2
  a. `grace_period = settings.CLUSTER_NODE_HEARTBEAT_PERIOD * settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE`
  b. if `last_seen` is before this grace period, mark instance as lost
4. Determine if *this* node is lost and run `local_health_check`
  a. call `get_cpu_count` and `get_mem_in_bytes` directly from ansible-runner, which is what `ansible-runner --worker-info` calls under the hood
5. If *this* instance was not found in the database, register it
6. Compare *this* node's ansible-runner version with that of other instances
  a. if this version is older, call `stop_local_services` which shuts down itself
7. For other instances marked as lost (step 3)
  a. reap running, pending, and waiting jobs on that instance (mark them as failed)
  b. delete instance from DB instance list
8. `cluster_node_heartbeat` is called from the dispatcher, and the dispatcher parent process passes `worker_tasks` data to this method
  a. reap local jobs that are not active (that is, no dispatcher worker is actively processing it)

## Instance groups

As mentioned, control and execution nodes are registered in the database as instances. These instances can be groups into instance groups via the API.

## Configuring Instances and Instance Groups from the API

Instance Groups can be created by posting to `/api/v2/instance_groups` as a System Administrator.

Once created, `Instances` can be associated with an Instance Group with:

```
HTTP POST /api/v2/instance_groups/x/instances/ {'id': y}`
```

An `Instance` that is added to an `InstanceGroup` will automatically reconfigure itself to listen on the group's work queue. See the following section `Instance Group Policies` for more details.


### Instance Group Policies

AWX `Instances` can be configured to automatically join `Instance Groups` when they come online by defining a policy. These policies are evaluated for
every new Instance that comes online.

Instance Group Policies are controlled by three optional fields on an `Instance Group`:

- `policy_instance_percentage`: This is a number between 0 - 100. It guarantees that this percentage of active AWX instances will be added to this `Instance Group`. As new instances come online, if the number of Instances in this group relative to the total number of instances is fewer than the given percentage, then new ones will be added until the percentage condition is satisfied.
- `policy_instance_minimum`: This policy attempts to keep at least this many `Instances` in the `Instance Group`. If the number of available instances is lower than this minimum, then all `Instances` will be placed in this `Instance Group`.
- `policy_instance_list`: This is a fixed list of `Instance` names to always include in this `Instance Group`.

- `Instances` that are assigned directly to `Instance Groups` by posting to `/api/v2/instance_groups/x/instances` or `/api/v2/instances/x/instance_groups` are automatically added to the `policy_instance_list`. This means they are subject to the normal caveats for `policy_instance_list` and must be manually managed.

- `policy_instance_percentage` and `policy_instance_minimum` work together. For example, if you have a `policy_instance_percentage` of 50% and a `policy_instance_minimum` of 2 and you start 6 `Instances`, 3 of them would be assigned to the `Instance Group`. If you reduce the number of `Instances` to 2, then both of them would be assigned to the `Instance Group` to satisfy `policy_instance_minimum`. In this way, you can set a lower bound on the amount of available resources.

- Policies don't actively prevent `Instances` from being associated with multiple `Instance Groups` but this can effectively be achieved by making the percentages sum to 100. If you have 4 `Instance Groups`, assign each a percentage value of 25 and the `Instances` will be distributed among them with no overlap.


### Manually Pinning Instances to Specific Groups

If you have a special `Instance` which needs to be _exclusively_ assigned to a specific `Instance Group` but don't want it to automatically join _other_ groups via "percentage" or "minimum" policies:

1. Add the `Instance` to one or more `Instance Group`s' `policy_instance_list`.
2. Update the `Instance`'s `managed_by_policy` property to be `False`.

This will prevent the `Instance` from being automatically added to other groups based on percentage and minimum policy; it will **only** belong to the groups you've manually assigned it to:

```
HTTP PATCH /api/v2/instance_groups/N/
{
    "policy_instance_list": ["special-instance"]
}

HTTP PATCH /api/v2/instances/X/
{
    "managed_by_policy": False
}
```


### Status and Monitoring

AWX itself reports as much status as it can via the API at `/api/v2/ping` in order to provide validation of the health of the cluster. This includes:

- The instance servicing the HTTP request.
- The last heartbeat time of all other instances in the cluster.
- Instance Groups and Instance membership in those groups.

A more detailed view of Instances and Instance Groups, including running jobs and membership
information can be seen at `/api/v2/instances/` and `/api/v2/instance_groups`.

### Job Runtime Behavior

Ideally a regular user of AWX should not notice any semantic difference to the way jobs are run and reported. Behind the scenes it is worth pointing out the differences in how the system behaves.

When a job is submitted from the API interface, it gets pushed into the dispatcher queue via postgres notify/listen (https://www.postgresql.org/docs/10/sql-notify.html), and the task is handled by the dispatcher process running on that specific AWX node.  If an instance fails while executing jobs, then the work is marked as permanently failed.

If a cluster is divided into separate Instance Groups, then the behavior is similar to the cluster as a whole. If two instances are assigned to a group then either one is just as likely to receive a job as any other in the same group.

As AWX instances are brought online, it effectively expands the work capacity of the AWX system. If those instances are also placed into Instance Groups, then they also expand that group's capacity. If an instance is performing work and it is a member of multiple groups, then capacity will be reduced from all groups for which it is a member. De-provisioning an instance will remove capacity from the cluster wherever that instance was assigned.

It's important to note that not all instances are required to be provisioned with an equal capacity.

If an Instance Group is configured but all instances in that group are offline or unavailable, any jobs that are launched targeting only that group will be stuck in a waiting state until instances become available. Fallback or backup resources should be provisioned to handle any work that might encounter this scenario.

#### Project Synchronization Behavior

It is important that project updates run on the instance which prepares the ansible-runner private data directory.
This is accomplished by a project sync which is done by the dispatcher control / launch process.
The sync will update the source tree to the correct version on the instance immediately prior to transmitting the job.
If the needed revision is already locally checked out and Galaxy or Collections updates are not needed, then a sync may not be performed.

When the sync happens, it is recorded in the database as a project update with a `launch_type` of "sync" and a `job_type` of "run". Project syncs will not change the status or version of the project; instead, they will update the source tree _only_ on the instance where they run. The only exception to this behavior is when the project is in the "never updated" state (meaning that no project updates of any type have been run), in which case a sync should fill in the project's initial revision and status, and subsequent syncs should not make such changes.

All project updates run with container isolation (like jobs) and volume mount to the persistent projects folder.

#### Controlling Where a Particular Job Runs

By default, a job will be submitted to the default queue (formerly the `tower` queue).
To see the name of the queue, view the setting `DEFAULT_EXECUTION_QUEUE_NAME`.
Administrative actions, like project updates, will run in the control plane queue.
The name of the control plane queue is surfaced in the setting `DEFAULT_CONTROL_PLANE_QUEUE_NAME`.


##### How to Restrict the Instances a Job Will Run On

If the Job Template, Inventory, or Organization have instance groups associated with them, a job run from that Job Template will not be eligible for the default behavior. This means that if all of the instance associated with these three resources are out of capacity, the job will remain in the `pending` state until capacity frees up.


##### How to Set Up a Preferred Instance Group

The order of preference in determining which instance group the job gets submitted to is as follows:

1. Job Template
2. Inventory
3. Organization (by way of Inventory)

To expand further: If instance groups are associated with the Job Template and all of them are at capacity, then the job will be submitted to instance groups specified on Inventory, and then Organization.

The global `tower` group can still be associated with a resource, just like any of the custom instance groups defined in the playbook. This can be used to specify a preferred instance group on the job template or inventory, but still allow the job to be submitted to any instance if those are out of capacity.


#### Instance Enable / Disable

In order to support temporarily taking an `Instance` offline, there is a boolean property `enabled` defined on each instance.

When this property is disabled, no jobs will be assigned to that `Instance`. Existing jobs will finish but no new work will be assigned.
