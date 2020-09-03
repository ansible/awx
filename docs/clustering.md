## Tower Clustering/HA Overview

Prior to 3.1, the Ansible Tower HA solution was not a true high-availability system. This system has been entirely rewritten in 3.1 with a focus towards a proper highly-available clustered system. This has been extended further in 3.2 to allow grouping of clustered instances into different pools/queues.

* Each instance should be able to act as an entry point for UI and API Access.
  This should enable Tower administrators to use load balancers in front of as many instances as they wish and maintain good data visibility.
* Each instance should be able to join the Tower cluster and expand its ability to execute jobs.
* Provisioning new instance should be as simple as updating the `inventory` file and re-running the setup playbook.
* Instances can be de-provisioned with a simple management command.
* Instances can be grouped into one or more Instance Groups to share resources for topical purposes.
* These instance groups should be assignable to certain resources:
  * Organizations
  * Inventories
  * Job Templates

  ...such that execution of jobs under those resources will favor particular queues.

It's important to point out a few existing things:

* PostgreSQL is still a standalone instance and is not clustered. Replica configuration will not be managed. If the user configures standby replicas, database failover will also not be managed.
* All instances should be reachable from all other instances and they should be able to reach the database. It's also important for the hosts to have a stable address and/or hostname (depending on how you configure the Tower host).
* Existing old-style HA deployments will be transitioned automatically to the new HA system during the upgrade process to 3.1.
* Manual projects will need to be synced to all instances by the customer.

Ansible Tower 3.3 adds support for container-based clusters using Openshift or Kubernetes.


## Important Changes

* There is no concept of primary/secondary in the new Tower system. *All* systems are primary.
* The `inventory` file for Tower deployments should be saved/persisted. If new instances are to be provisioned, the passwords and configuration options as well as host names will need to be available to the installer.


## Concepts and Configuration

### Installation and the Inventory File
The current standalone instance configuration doesn't change for a 3.1+ deployment. The inventory file does change in some important ways:

* Since there is no primary/secondary configuration, those inventory groups go away and are replaced with a single inventory group `tower`. The customer may *optionally* define other groups and group instances in those groups. These groups should be prefixed with `instance_group_`. Instances are not required to be in the `tower` group alongside other `instance_group_` groups, but one instance *must* be present in the `tower` group. Technically `tower` is a group like any other `instance_group_` group, but it must always be present and if a specific group is not associated with a specific resource, then job execution will always fall back to the `tower` group:

```
[tower]
hostA
hostB
hostC

[instance_group_east]
hostB
hostC

[instance_group_west]
hostC
hostD
```

The `database` group remains in order to specify an external Postgres. If the database host is provisioned separately, this group should be empty.

```
[tower]
hostA
hostB
hostC

[database]
hostDB
```


Recommendations and constraints:
 - Do not create a group named `instance_group_tower`.
 - Do not name any instance the same as a group name.


### Security-Isolated Rampart Groups

In Tower versions 3.2+, customers may optionally define isolated groups inside of security-restricted networking zones from which to run jobs and ad hoc commands. Instances in these groups will _not_ have a full install of Tower, but will have a minimal set of utilities used to run jobs. Isolated groups must be specified in the inventory file prefixed with `isolated_group_`. An example inventory file is shown below:

```
[tower]
towerA
towerB
towerC

[instance_group_security]
towerB
towerC

[isolated_group_govcloud]
isolatedA
isolatedB

[isolated_group_govcloud:vars]
controller=security
```

In the isolated rampart model, "controller" instances interact with "isolated" instances via a series of Ansible playbooks over SSH.  At installation time, a randomized RSA key is generated and distributed as an authorized key to all "isolated" instances.  The private half of the key is encrypted and stored within Tower, and is used to authenticate from "controller" instances to "isolated" instances when jobs are run.

When a job is scheduled to run on an "isolated" instance:

*  The "controller" instance compiles metadata required to run the job and copies it to the "isolated" instance via `rsync` (any related project or inventory updates are run on the controller instance). This metadata includes:

   - the entire SCM checkout directory for the project
   - a static inventory file
   - pexpect passwords
   - environment variables
   - the `ansible`/`ansible-playbook` command invocation, _i.e._, `bwrap ... ansible-playbook -i /path/to/inventory /path/to/playbook.yml -e ...`

* Once the metadata has been `rsync`ed to the isolated host, the "controller instance" starts a process on the "isolated" instance which consumes the metadata and starts running `ansible`/`ansible-playbook`.  As the playbook runs, job artifacts (such as `stdout` and job events) are written to disk on the "isolated" instance.

* While the job runs on the "isolated" instance, the "controller" instance periodically copies job artifacts (`stdout` and job events) from the "isolated" instance using `rsync`.  It consumes these until the job finishes running on the "isolated" instance.

Isolated groups are architected such that they may exist inside of a VPC with security rules that _only_ permit the instances in its `controller` group to access them; only ingress SSH traffic from "controller" instances to "isolated" instances is required.

Recommendations for system configuration with isolated groups:
 - Do not create a group named `isolated_group_tower`.
 - Do not put any isolated instances inside the `tower` group or other ordinary instance groups.
 - Define the `controller` variable as either a group var or as a hostvar on all the instances in the isolated group. Please _do not_ allow isolated instances in the same group have a different value for this variable - the behavior in this case can not be predicted.
 - Do not put an isolated instance in more than one isolated group.


Isolated Instance Authentication
--------------------------------
At installation time, by default, a randomized RSA key is generated and distributed as an authorized key to all "isolated" instances.  The private half of the key is encrypted and stored within Tower, and is used to authenticate from "controller" instances to "isolated" instances when jobs are run.

For users who wish to manage SSH authentication from controlling instances to isolated instances via some system _outside_ of Tower (such as externally-managed, password-less SSH keys), this behavior can be disabled by unsetting two Tower API settings values:

`HTTP PATCH /api/v2/settings/jobs/ {'AWX_ISOLATED_PRIVATE_KEY': '', 'AWX_ISOLATED_PUBLIC_KEY': ''}`


### Provisioning and Deprovisioning Instances and Groups

* **Provisioning** - Provisioning Instances after installation is supported by updating the `inventory` file and re-running the setup playbook. It's important that this file contain all passwords and information used when installing the cluster, or other instances may be reconfigured (this can be done intentionally).

* **Deprovisioning** - Tower does not automatically de-provision instances since it cannot distinguish between an instance that was taken offline intentionally or due to failure. Instead, the procedure for de-provisioning an instance is to shut it down (or stop the `ansible-tower-service`) and run the Tower de-provision command:

```
$ awx-manage deprovision_instance --hostname=<hostname>
```

* **Removing/Deprovisioning Instance Groups** - Tower does not automatically de-provision or remove instance groups, even though re-provisioning will often cause these to be unused. They may still show up in API endpoints and stats monitoring. These groups can be removed with the following command:

```
$ awx-manage unregister_queue --queuename=<name>
```

### Configuring Instances and Instance Groups from the API

Instance Groups can be created by posting to `/api/v2/instance_groups` as a System Administrator.

Once created, `Instances` can be associated with an Instance Group with:

```
HTTP POST /api/v2/instance_groups/x/instances/ {'id': y}`
```

An `Instance` that is added to an `InstanceGroup` will automatically reconfigure itself to listen on the group's work queue. See the following section `Instance Group Policies` for more details.


### Instance Group Policies

Tower `Instances` can be configured to automatically join `Instance Groups` when they come online by defining a policy. These policies are evaluated for
every new Instance that comes online.

Instance Group Policies are controlled by three optional fields on an `Instance Group`:

* `policy_instance_percentage`: This is a number between 0 - 100. It guarantees that this percentage of active Tower instances will be added to this `Instance Group`. As new instances come online, if the number of Instances in this group relative to the total number of instances is fewer than the given percentage, then new ones will be added until the percentage condition is satisfied.
* `policy_instance_minimum`: This policy attempts to keep at least this many `Instances` in the `Instance Group`. If the number of available instances is lower than this minimum, then all `Instances` will be placed in this `Instance Group`.
* `policy_instance_list`: This is a fixed list of `Instance` names to always include in this `Instance Group`.

> NOTES

* `Instances` that are assigned directly to `Instance Groups` by posting to `/api/v2/instance_groups/x/instances` or `/api/v2/instances/x/instance_groups` are automatically added to the `policy_instance_list`. This means they are subject to the normal caveats for `policy_instance_list` and must be manually managed.

* `policy_instance_percentage` and `policy_instance_minimum` work together. For example, if you have a `policy_instance_percentage` of 50% and a `policy_instance_minimum` of 2 and you start 6 `Instances`, 3 of them would be assigned to the `Instance Group`. If you reduce the number of `Instances` to 2, then both of them would be assigned to the `Instance Group` to satisfy `policy_instance_minimum`. In this way, you can set a lower bound on the amount of available resources.

* Policies don't actively prevent `Instances` from being associated with multiple `Instance Groups` but this can effectively be achieved by making the percentages sum to 100. If you have 4 `Instance Groups`, assign each a percentage value of 25 and the `Instances` will be distributed among them with no overlap.


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

Tower itself reports as much status as it can via the API at `/api/v2/ping` in order to provide validation of the health of the Cluster. This includes:

* The instance servicing the HTTP request.
* The last heartbeat time of all other instances in the cluster.
* Instance Groups and Instance membership in those groups.

A more detailed view of Instances and Instance Groups, including running jobs and membership
information can be seen at `/api/v2/instances/` and `/api/v2/instance_groups`.


### Instance Services and Failure Behavior

Each Tower instance is made up of several different services working collaboratively:

* **HTTP Services** - This includes the Tower application itself as well as external web services.
* **Callback Receiver** - Receives job events that result from running Ansible jobs.
* **Celery** - The worker queue that processes and runs all jobs.
* **Redis** - this is used as a queue for AWX to process ansible playbook callback events.

Tower is configured in such a way that if any of these services or their components fail, then all services are restarted. If these fail sufficiently (often in a short span of time), then the entire instance will be placed offline in an automated fashion in order to allow remediation without causing unexpected behavior.


### Job Runtime Behavior

Ideally a regular user of Tower should not notice any semantic difference to the way jobs are run and reported. Behind the scenes it is worth pointing out the differences in how the system behaves.

When a job is submitted from the API interface, it gets pushed into the dispatcher queue via postgres notify/listen (https://www.postgresql.org/docs/10/sql-notify.html), and the task is handled by the dispatcher process running on that specific Tower node.  If an instance fails while executing jobs, then the work is marked as permanently failed.

If a cluster is divided into separate Instance Groups, then the behavior is similar to the cluster as a whole. If two instances are assigned to a group then either one is just as likely to receive a job as any other in the same group.

As Tower instances are brought online, it effectively expands the work capacity of the Tower system. If those instances are also placed into Instance Groups, then they also expand that group's capacity. If an instance is performing work and it is a member of multiple groups, then capacity will be reduced from all groups for which it is a member. De-provisioning an instance will remove capacity from the cluster wherever that instance was assigned.

It's important to note that not all instances are required to be provisioned with an equal capacity.

If an Instance Group is configured but all instances in that group are offline or unavailable, any jobs that are launched targeting only that group will be stuck in a waiting state until instances become available. Fallback or backup resources should be provisioned to handle any work that might encounter this scenario.

#### Project Synchronization Behavior

Project updates behave differently than they did before. Previously they were ordinary jobs that ran on a single instance. It's now important that they run successfully on any instance that could potentially run a job. Projects will sync themselves to the correct version on the instance immediately prior to running the job. If the needed revision is already locally checked out and Galaxy or Collections updates are not needed, then a sync may not be performed.

When the sync happens, it is recorded in the database as a project update with a `launch_type` of "sync" and a `job_type` of "run". Project syncs will not change the status or version of the project; instead, they will update the source tree _only_ on the instance where they run. The only exception to this behavior is when the project is in the "never updated" state (meaning that no project updates of any type have been run), in which case a sync should fill in the project's initial revision and status, and subsequent syncs should not make such changes.

#### Controlling Where a Particular Job Runs

By default, a job will be submitted to the `tower` queue, meaning that it can be picked up by any of the workers.


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

## Acceptance Criteria

When verifying acceptance, we should ensure that the following statements are true:

* Tower should install as a standalone Instance
* Tower should install in a Clustered fashion
* Instances should, optionally, be able to be grouped arbitrarily into different Instance Groups
* Capacity should be tracked at the group level and capacity impact should make sense relative to what instance a job is running on and what groups that instance is a member of
* Provisioning should be supported via the setup playbook
* De-provisioning should be supported via a management command
* All jobs, inventory updates, and project updates should run successfully
* Jobs should be able to run on hosts for which they are targeted; if assigned implicitly or directly to groups, then they should only run on instances in those Instance Groups
* Project updates should manifest their data on the host that will run the job immediately prior to the job running
* Tower should be able to reasonably survive the removal of all instances in the cluster
* Tower should behave in a predictable fashion during network partitioning

## Testing Considerations

* Basic testing should be able to demonstrate parity with a standalone instance for all integration testing.
* Basic playbook testing to verify routing differences, including:
  - Basic FQDN
  - Short-name name resolution
  - IP addresses
  - `/etc/hosts` static routing information
* We should test behavior of large and small clusters; small clusters usually consist of 2 - 3 instances and large clusters have 10 - 15 instances.
* Failure testing should involve killing single instances and killing multiple instances while the cluster is performing work. Job failures during the time period should be predictable and not catastrophic.
* Instance downtime testing should also include recoverability testing (killing single services and ensuring the system can return itself to a working state).
* Persistent failure should be tested by killing single services in such a way that the cluster instance cannot be recovered and ensuring that the instance is properly taken offline.
* Network partitioning failures will also be important. In order to test this:
  - Disallow a single instance from communicating with the other instances but allow it to communicate with the database
  - Break the link between instances such that it forms two or more groups where Group A and Group B can't communicate but all instances can communicate with the database.
* Crucially, when network partitioning is resolved, all instances should recover into a consistent state.
* Upgrade Testing - verify behavior before and after are the same for the end user.
* Project Updates should be thoroughly tested for all SCM types (`git`, `svn`, `hg`) and for manual projects.
* Setting up instance groups in two scenarios:
  a) instances are shared between groups
  b) instances are isolated to particular groups
  Organizations, Inventories, and Job Templates should be variously assigned to one or many groups and jobs should execute in those groups in preferential order as resources are available.

## Performance Testing

Performance testing should be twofold:

* A large volume of simultaneous jobs
* Jobs that generate a large amount of output

These should also be benchmarked against the same playbooks using the 3.0.X Tower release and a stable Ansible version. For a large volume playbook (*e.g.*, against 100+ hosts), something like the following is recommended:

https://gist.github.com/michelleperz/fe3a0eb4eda888221229730e34b28b89
