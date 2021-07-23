## Receptor Mesh

AWX uses a Receptor mesh to transmit "user-space" unified jobs:
 - jobs
 - ad hoc commands
 - inventory updates

to the node where they run.

https://github.com/ansible/receptor

> NOTE: user-space jobs are what carry out the user's Ansible automation. These job types run inside of the designated execution environment so that the needed content is available.

### Split of Control Plane versus Execution Plane

Instances in the control plane run persistent AWX services (like the web server, task dispatcher, etc.), project updates, and management jobs.

Hybrid instances in the control plane may also run user-space jobs.

The unified jobs API reports `controller_node` and `execution_node` fields.
The execution node is where the job runs. The controller node prepares the private_data_dir for the job, and processes the receptor output stream.

#### Receptor Configuration

Execution nodes (all nodes that can run jobs) need to advertise the "ansible-runner" work type.
All user-space jobs are submitted as a receptor work unit with this work type.

An entry like this should appear in its `receptor.conf` (receptor configuration file):

```
- work-command:
    worktype: ansible-runner
    command: ansible-runner
    params: worker
    allowruntimeparams: true
```

Control (and hybrid) nodes need to advertise the "local" work type.
Project updates are submitted as this work type.

```
- work-command:
    worktype: local
    command: ansible-runner
    params: worker
    allowruntimeparams: true
```

If user-space jobs run on a hybrid node, they will also run as the "local" work type.

After the initial receptor integration, but before the control plane and execution plane split, all job types ran as the "local" work type on the same node as the control node.

If ran in a container_group, user-space jobs run as the "kubernetes-runtime-auth" work type.

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
