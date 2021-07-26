## Receptor Mesh

AWX uses a [Receptor](https://github.com/ansible/receptor) mesh to transmit "user-space" unified jobs:
 - jobs
 - ad hoc commands
 - inventory updates

to the node where they run.

> NOTE: user-space jobs are what carry out the user's Ansible automation. These job types run inside of the designated execution environment so that the needed content is available.

> NOTE: The word "node" corresponds to entries in the `Instance` database model, or the `/api/v2/instances/` endpoint, and is a machine participating in the cluster / mesh.

### Split of Control Plane versus Execution Plane

Instances in the control plane run persistent AWX services (like the web server, task dispatcher, etc.), project updates, and management jobs.

Hybrid instances in the control plane may also run user-space jobs.
The task manager logic will not send user-space jobs to control-only nodes.

The unified jobs API reports `controller_node` and `execution_node` fields.
The execution node is where the job runs. The controller node prepares the `private_data_dir` for the job, and processes the receptor output stream.

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

After the initial receptor integration, but before the control plane and execution plane split, all job types ran as the "local" work type on the same node as the control node.

Here is a listing of work types that you may encounter:

 - `local` - any ansible-runner job ran in a traditional install
 - `ansible-runner` - remote execution of user-space jobs
 - `kubernetes-runtime-auth` - user-space jobs ran in a container group
 - `kubernetes-runtime-auth` - project updates and management jobs on OpenShift Container Platform

### Auto-discovery of execution nodes

Instances in control plane must be registered by the installer via `awx-manage`
commands like `awx-manage register_queue` or `awx-manage register_instance`.

Execution-only nodes are automatically discovered after they have been configured and join the receptor mesh.
Control nodes should see them as a "Known Node".

Control nodes check the receptor network (reported via `receptorctl status`) when their heartbeat task runs.
Nodes on the receptor network are compared against the `Instance` model in the database.

If a node appears in the mesh network which is not in the database, then a "health check" is started.
This will submit a work unit to the execution node which then outputs important node data via `ansible-runner`.
The `capacity` field will obtain a non-zero value through this process, which is necessary to run jobs.
