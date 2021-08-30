## Receptor Mesh

AWX uses a [Receptor](https://github.com/ansible/receptor) mesh to transmit "user-space" unified jobs:
 - jobs
 - ad hoc commands
 - inventory updates

to the node where they run.

> NOTE: user-space jobs are what carry out the user's Ansible automation. These job types run inside of the designated execution environment so that the needed content is available.

> NOTE: The word "node" corresponds to entries in the `Instance` database model, or the `/api/v2/instances/` endpoint, and is a machine participating in the cluster / mesh.

The unified jobs API reports `controller_node` and `execution_node` fields.
The execution node is where the job runs, and the controller node interfaces between the job and server functions.

Before a job can start, the controller node prepares the `private_data_dir` needed for the job to run.
Next, the controller node sends the data via `ansible-runner`'s `transmit`, and connects to the output stream with `process`.
For details on these commands, see the [ansible-runner docs on remote execution](https://ansible-runner.readthedocs.io/en/latest/remote_jobs.html).

On the other side, the execution node runs the job under `ansible-runner worker`.

### Split of Control Plane versus Execution Plane

Instances in the **control plane** run persistent AWX services (like the web server, task dispatcher, etc.), project updates, and management jobs.

The task manager logic will not send user-space jobs to **control-only** nodes.
In the inventory definition, the user can set a flag to designate this node type.

**Execution-only** nodes have a minimal set of software requirements needed to participate in the receptor mesh and run jobs under ansible-runner with podman isolation.
These _only_ run user-space jobs, and may be geographically separated (with high latency) from the control plane.
They may not even have a direct connection to the cluster, and use other receptor **hop** nodes to communicate.
The hop and execution-only nodes may be referred to collectively as the **execution plane**.

**Hybrid** (control & execution nodes) are instances in the control plane that are allowed to run user-space jobs.

#### Receptor Configuration Work Type

Execution-only nodes need to advertise the "ansible-runner" work type.
User-space jobs are submitted as a receptor work unit with this work type.

An entry like this should appear in its `receptor.conf` (receptor configuration file):

```
- work-command:
    worktype: ansible-runner
    command: ansible-runner
    params: worker
    allowruntimeparams: true
```

Control (and hybrid) nodes advertise the "local" work type instead.
So the entry is the same as above, except that it has `worktype: local`.
Project updates are submitted as this work type.
If user-space jobs run on a hybrid node, they will also run as the "local" work type.

Here is a listing of work types that you may encounter:

 - `local` - any ansible-runner job ran in a traditional install
 - `ansible-runner` - remote execution of user-space jobs
 - `kubernetes-runtime-auth` - user-space jobs ran in a container group
 - `kubernetes-incluster-auth` - project updates and management jobs on OpenShift Container Platform

### Auto-discovery of execution nodes

Instances in control plane must be registered by the installer via `awx-manage`
commands like `awx-manage register_queue` or `awx-manage register_instance`.

Execution-only nodes are automatically discovered after they have been configured and join the receptor mesh.
Control nodes should see them as a "Known Node".

Control nodes check the receptor network (reported via `receptorctl status`) when their heartbeat task runs.
Nodes on the receptor network are compared against the `Instance` model in the database.

If a node appears in the mesh network which is not in the database, then a "health check" is started.
The `capacity` field will obtain a non-zero value through this process, which is necessary to run jobs.

#### Health Check Mechanics

All relevant data for health checks is reported from the ansible-runner command:

```
ansible-runner worker --worker-info
```

This will output YAML data to standard out containing CPU, memory, and other metrics used to compute `capacity`.

AWX invokes this command by submitting a receptor work unit (of type `ansible-runner`) to the target execution node.
If you have the development environment running, you can run a one-off health check of a node with this command:

```
echo "from awx.main.utils.receptor import worker_info; worker_info('receptor-1')" | awx-manage shell_plus --quiet
```

This must be ran as the awx user inside one of the hybrid or control nodes.
This will not affect actual `Instance` record, but will just run the command and report the data.

### Development Environment

A cluster (of containers) with execution nodes and a hop node is created by the docker-compose Makefile target.
By default, it will create 1 hybrid node, 1 hop node, and 2 execution nodes.
You can switch the type of AWX nodes between hybrid and control with this syntax.

```
MAIN_NODE_TYPE=control COMPOSE_TAG=devel make docker-compose
```

Running the above command will create a cluster of 1 control node, 1 hop node, and 2 execution nodes.


The number of nodes can be changed:

```
CONTROL_PLANE_NODE_COUNT=2 EXECUTION_NODE_COUNT=3 COMPOSE_TAG=devel make docker-compose
```

This will spin up a topology represented below.
(names are the receptor node names, which differ from the AWX Instance names and network address in some cases)

```
                                            ┌──────────────┐
                                            │              │
┌──────────────┐                 ┌──────────┤  receptor-1  │
│              │                 │          │              │
│    awx_1     │◄──────────┐     │          └──────────────┘
│              │           │     ▼
└──────┬───────┘    ┌──────┴───────┐        ┌──────────────┐
       │            │              │        │              │
       │            │ receptor-hop │◄───────┤  receptor-2  │
       ▼            │              │        │              │
┌──────────────┐    └──────────────┘        └──────────────┘
│              │                 ▲
│    awx_2     │                 │          ┌──────────────┐
│              │                 │          │              │
└──────────────┘                 └──────────┤  receptor-3  │
                                            │              │
                                            └──────────────┘
```

All execution (`receptor-*`) nodes connect to the hop node.
Only the `awx_1` node connects to the hop node out of the AWX cluster.
`awx_1` connects to `awx_2`, fulfilling the requirement that the AWX cluster is fully connected.

For an example, if a job is launched with `awx_2` as the `controller_node` and `receptor-3` as the `execution_node`,
then `awx_2` communicates to `receptor-3` via `awx_1` and then `receptor-hop`.
