## Tower Clustering/HA Overview

Prior to 3.1 the Ansible Tower HA solution was not a true high-availability system. In 3.1 we have rewritten this system entirely with a new focus towards
a proper highly available clustered system. In 3.2 we have extended this further to allow grouping of clustered instances into different pools/queues.

* Each instance should be able to act as an entrypoint for UI and API Access.
  This should enable Tower administrators to use load balancers in front of as many instances as they wish
  and maintain good data visibility.
* Each instance should be able to join the Tower cluster and expand its ability to execute jobs.
* Provisioning new instance should be as simple as updating the `inventory` file and re-running the setup playbook
* Instances can be deprovisioned with a simple management commands
* Instances can be grouped into one or more Instance Groups to share resources for topical purposes.
* These instance groups should be assignable to certain resources:
  * Organizations
  * Inventories
  * Job Templates
  such that execution of jobs under those resources will favor particular queues

It's important to point out a few existing things:

* PostgreSQL is still a standalone instance and is not clustered. We also won't manage replica configuration or,
  if the user configures standby replicas, database failover.
* All instances should be reachable from all other instances and they should be able to reach the database. It's also important
  for the hosts to have a stable address and/or hostname (depending on how you configure the Tower host)
* RabbitMQ is the cornerstone of Tower's Clustering system. A lot of our configuration requirements and behavior is dictated
  by its needs. Thus we are pretty inflexible to customization beyond what our setup playbook allows. Each Tower instance has a
  deployment of RabbitMQ that will cluster with the other instances' RabbitMQ instances.
* Existing old-style HA deployments will be transitioned automatically to the new HA system during the upgrade process to 3.1.
* Manual projects will need to be synced to all instances by the customer

## Important Changes

* There is no concept of primary/secondary in the new Tower system. *All* systems are primary.
* Setup playbook changes to configure rabbitmq and give hints to the type of network the hosts are on.
* The `inventory` file for Tower deployments should be saved/persisted. If new instances are to be provisioned
  the passwords and configuration options as well as host names will need to be available to the installer.

## Concepts and Configuration

### Installation and the Inventory File
The current standalone instance configuration doesn't change for a 3.1+ deploy. The inventory file does change in some important ways:

* Since there is no primary/secondary configuration those inventory groups go away and are replaced with a
  single inventory group `tower`. The customer may, *optionally*, define other groups and group instances in those groups. These groups
  should be prefixed with `instance_group_`. Instances are not required to be in the `tower` group alongside other `instance_group_` groups, but one
  instance *must* be present in the `tower` group. Technically `tower` is a group like any other `instance_group_` group but it must always be present
  and if a specific group is not associated with a specific resource then job execution will always fall back to the `tower` group:
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
  
  The `database` group remains for specifying an external postgres. If the database host is provisioned seperately this group should be empty
  ```
  [tower]
  hostA
  hostB
  hostC
  
  [database]
  hostDB
  ```

* It's common for customers to provision Tower instances externally but prefer to reference them by internal addressing. This is most significant
  for RabbitMQ clustering where the service isn't available at all on an external interface. For this purpose it is necessary to assign the internal
  address for RabbitMQ links as such:
  ```
  [tower]
  hostA rabbitmq_host=10.1.0.2
  hostB rabbitmq_host=10.1.0.3
  hostC rabbitmq_host=10.1.0.3
  ```
* The `redis_password` field is removed from `[all:vars]`
* There are various new fields for RabbitMQ:
  - `rabbitmq_port=5672` - RabbitMQ is installed on each instance and is not optional, it's also not possible to externalize. It is
    possible to configure what port it listens on and this setting controls that.
  - `rabbitmq_vhost=tower` - Tower configures a rabbitmq virtualhost to isolate itself. This controls that settings.
  - `rabbitmq_username=tower` and `rabbitmq_password=tower` - Each instance will be configured with these values and each instance's Tower
    instance will be configured with it also. This is similar to our other uses of usernames/passwords.
  - `rabbitmq_cookie=<somevalue>` - This value is unused in a standalone deployment but is critical for clustered deployments.
    This acts as the secret key that allows RabbitMQ cluster members to identify each other.
  - `rabbitmq_use_long_names` - RabbitMQ is pretty sensitive to what each instance is named. We are flexible enough to allow FQDNs
    (host01.example.com), short names (host01), or ip addresses (192.168.5.73). Depending on what is used to identify each host
    in the `inventory` file this value may need to be changed. For FQDNs and ip addresses this value needs to be `true`. For short
    names it should be `false`
  - `rabbitmq_enable_manager` - Setting this to `true` will expose the RabbitMQ management web console on each instance.

The most important field to point out for variability is `rabbitmq_use_long_name`. That's something we can't detect or provide a reasonable
default for so it's important to point out when it needs to be changed. If instances are provisioned to where they reference other instances
internally and not on external addressess then `rabbitmq_use_long_name` semantics should follow the internal addressing (aka `rabbitmq_host`.

Other than `rabbitmq_use_long_name` the defaults are pretty reasonable:
```
rabbitmq_port=5672
rabbitmq_vhost=tower
rabbitmq_username=tower
rabbitmq_password=''
rabbitmq_cookie=cookiemonster

# Needs to be true for fqdns and ip addresses
rabbitmq_use_long_name=false
rabbitmq_enable_manager=false
```

Recommendations and constraints:
 - Do not create a group named `instance_group_tower`
 - Do not name any instance the same as a group name

### Security Isolated Rampart Groups

In Tower versions 3.2+ customers may optionally define isolated groups
inside security-restricted networking zones to run jobs and ad hoc commands from.
Instances in these groups will _not_ have a full install of Tower, but will have a minimal
set of utilities used to run jobs. Isolated groups must be specified
in the inventory file prefixed with `isolated_group_`. An example inventory
file is shown below.

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

In the isolated rampart model, "controller" instances interact with "isolated"
instances via a series of Ansible playbooks over SSH.  At installation time,
a randomized RSA key is generated and distributed as an authorized key to all
"isolated" instances.  The private half of the key is encrypted and stored
within Tower, and is used to authenticate from "controller" instances to
"isolated" instances when jobs are run.

When a job is scheduled to run on an "isolated" instance:

*  The "controller" instance compiles metadata required to run the job and copies
   it to the "isolated" instance via `rsync` (any related project or inventory
   updates are run on the controller instance). This metadata includes:

   - the entire SCM checkout directory for the project
   - a static inventory file
   - pexpect passwords
   - environment variables
   - the `ansible`/`ansible-playbook` command invocation, i.e., 
     `bwrap ... ansible-playbook -i /path/to/inventory /path/to/playbook.yml -e ...`

* Once the metadata has been rsynced to the isolated host, the "controller
  instance" starts a process on the "isolated" instance which consumes the
  metadata and starts running `ansible`/`ansible-playbook`.  As the playbook
  runs, job artifacts (such as stdout and job events) are written to disk on
  the "isolated" instance.

* While the job runs on the "isolated" instance, the "controller" instance
  periodically copies job artifacts (stdout and job events) from the "isolated"
  instance using `rsync`.  It consumes these until the job finishes running on the
  "isolated" instance.

Isolated groups are architected such that they may exist inside of a VPC
with security rules that _only_ permit the instances in its `controller`
group to access them; only ingress SSH traffic from "controller" instances to
"isolated" instances is required.

Recommendations for system configuration with isolated groups:
 - Do not create a group named `isolated_group_tower`
 - Do not put any isolated instances inside the `tower` group or other
   ordinary instance groups.
 - Define the `controller` variable as either a group var or as a hostvar
   on all the instances in the isolated group. Please _do not_ allow
   isolated instances in the same group have a different value for this
   variable - the behavior in this case can not be predicted.
 - Do not put an isolated instance in more than 1 isolated group.

Isolated Instance Authentication
--------------------------------
By default - at installation time - a randomized RSA key is generated and
distributed as an authorized key to all "isolated" instances.  The private half
of the key is encrypted and stored within Tower, and is used to authenticate
from "controller" instances to "isolated" instances when jobs are run.

For users who wish to manage SSH authentication from controlling instances to
isolated instances via some system _outside_ of Tower (such as externally-managed
passwordless SSH keys), this behavior can be disabled by unsetting two Tower
API settings values:

`HTTP PATCH /api/v2/settings/jobs/ {'AWX_ISOLATED_PRIVATE_KEY': '', 'AWX_ISOLATED_PUBLIC_KEY': ''}`


### Provisioning and Deprovisioning Instances and Groups

* Provisioning
Provisioning Instances after installation is supported by updating the `inventory` file and re-running the setup playbook. It's important that this file
contain all passwords and information used when installing the cluster or other instances may be reconfigured (This could be intentional)

* Deprovisioning
Tower does not automatically de-provision instances since we can't distinguish between an instance that was taken offline intentionally or due to failure.
Instead the procedure for deprovisioning an instance is to shut it down (or stop the `ansible-tower-service`) and run the Tower deprovision command:

```
$ awx-manage deprovision_instance --hostname=<hostname>
```

* Removing/Deprovisioning Instance Groups
Tower does not automatically de-provision or remove instance groups, even though re-provisioning will often cause these to be unused. They may still
show up in api endpoints and stats monitoring. These groups can be removed with the following command:

```
$ awx-manage unregister_queue --queuename=<name>
```

### Status and Monitoring

Tower itself reports as much status as it can via the api at `/api/v2/ping` in order to provide validation of the health
of the Cluster. This includes:

* The instance servicing the HTTP request
* The last heartbeat time of all other instances in the cluster
* The RabbitMQ cluster status
* Instance Groups and Instance membership in those groups

A more detailed view of Instances and Instance Groups, including running jobs and membership
information can be seen at `/api/v2/instances/` and `/api/v2/instance_groups`.

### Instance Services and Failure Behavior

Each Tower instance is made up of several different services working collaboratively:

* HTTP Services - This includes the Tower application itself as well as external web services.
* Callback Receiver - Whose job it is to receive job events from running Ansible jobs.
* Celery - The worker queue, that processes and runs all jobs.
* RabbitMQ - Message Broker, this is used as a signaling mechanism for Celery as well as any event data propogated to the application.
* Memcached - local caching service for the instance it lives on.

Tower is configured in such a way that if any of these services or their components fail then all services are restarted. If these fail sufficiently
often in a short span of time then the entire instance will be placed offline in an automated fashion in order to allow remediation without causing unexpected
behavior.

### Job Runtime Behavior

Ideally a regular user of Tower should not notice any semantic difference to the way jobs are run and reported. Behind the scenes its worth
pointing out the differences in how the system behaves.

When a job is submitted from the API interface it gets pushed into the Celery queue on RabbitMQ. A single RabbitMQ instance is the responsible master for
individual queues but each Tower instance will connect to and receive jobs from that queue using a Fair scheduling algorithm. Any instance on the cluster is 
just as likely to receive the work and execute the task. If a instance fails while executing jobs then the work is marked as permanently failed.

If a cluster is divided into separate Instance Groups then the behavior is similar to the cluster as a whole. If two instances are assigned to a group then
either one is just as likely to receive a job as any other in the same group.

As Tower instances are brought online it effectively expands the work capacity of the Tower system. If those instances are also placed into Instance Groups then
they also expand that group's capacity. If an instance is performing work and it is a member of multiple groups then capacity will be reduced from all groups for
which it is a member. De-provisioning an instance will remove capacity from the cluster wherever that instance was assigned.

It's important to note that not all instances are required to be provisioned with an equal capacity.

Project updates behave differently than they did before. Previously they were ordinary jobs that ran on a single instance. It's now important that
they run successfully on any instance that could potentially run a job. Project's will now sync themselves to the correct version on the instance immediately
prior to running the job.

If an Instance Group is configured but all instances in that group are offline or unavailable, any jobs that are launched targeting only that group will be stuck
in a waiting state until instances become available. Fallback or backup resources should be provisioned to handle any work that might encounter this scenario.

#### Controlling where a particular job runs

By default, a job will be submitted to the `tower` queue, meaning that it can be
picked up by any of the workers.

##### How to restrict the instances a job will run on

If any of the job template, inventory,
or organization has instance groups associated with them, a job ran from that job template
will not be eligible for the default behavior. That means that if all of the
instance associated with these 3 resources are out of capacity, the job will
remain in the `pending` state until capacity frees up.

##### How to set up a preferred instance group

The order of preference in determining which instance group to submit the job to
goes:

1. job template
2. inventory
3. organization (by way of inventory)

If instance groups are associated with the job template, and all of these
are at capacity, then the job will be submitted to instance groups specified
on inventory, and then organization.

The global `tower` group can still be associated with a resource, just like
any of the custom instance groups defined in the playbook. This can be
used to specify a preferred instance group on the job template or inventory,
but still allow the job to be submitted to any instance if those are out of
capacity.

## Acceptance Criteria

When verifying acceptance we should ensure the following statements are true

* Tower should install as a standalone Instance
* Tower should install in a Clustered fashion
* Instance should, optionally, be able to be grouped arbitrarily into different Instance Groups
* Capacity should be tracked at the group level and capacity impact should make sense relative to what instance a job is
  running on and what groups that instance is a member of.
* Provisioning should be supported via the setup playbook
* De-provisioning should be supported via a management command
* All jobs, inventory updates, and project updates should run successfully
* Jobs should be able to run on hosts which it is targeted. If assigned implicitly or directly to groups then it should
  only run on instances in those Instance Groups.
* Project updates should manifest their data on the host that will run the job immediately prior to the job running
* Tower should be able to reasonably survive the removal of all instances in the cluster
* Tower should behave in a predictable fashiong during network partitioning

## Testing Considerations

* Basic testing should be able to demonstrate parity with a standalone instance for all integration testing.
* Basic playbook testing to verify routing differences, including:
  - Basic FQDN
  - Short-name name resolution
  - ip addresses
  - /etc/hosts static routing information
* We should test behavior of large and small clusters. I would envision small clusters as 2 - 3 instances and large
  clusters as 10 - 15 instances
* Failure testing should involve killing single instances and killing multiple instances while the cluster is performing work.
  Job failures during the time period should be predictable and not catastrophic.
* Instance downtime testing should also include recoverability testing. Killing single services and ensuring the system can
  return itself to a working state
* Persistent failure should be tested by killing single services in such a way that the cluster instance cannot be recovered
  and ensuring that the instance is properly taken offline
* Network partitioning failures will be important also. In order to test this
  - Disallow a single instance from communicating with the other instances but allow it to communicate with the database
  - Break the link between instances such that it forms 2 or more groups where groupA and groupB can't communicate but all instances
    can communicate with the database.
* Crucially when network partitioning is resolved all instances should recover into a consistent state
* Upgrade Testing, verify behavior before and after are the same for the end user.
* Project Updates should be thoroughly tested for all scm types (git, svn, hg) and for manual projects.
* Setting up instance groups in two scenarios:
  a) instances are shared between groups
  b) instances are isolated to particular groups
  Organizations, Inventories, and Job Templates should be variously assigned to one or many groups and jobs should execute
  in those groups in preferential order as resources are available. 

## Performance Testing

Performance testing should be twofold.

* Large volume of simultaneous jobs.
* Jobs that generate a large amount of output.

These should also be benchmarked against the same playbooks using the 3.0.X Tower release and a stable Ansible version.
For a large volume playbook I might recommend a customer provided one that we've seen recently:

https://gist.github.com/michelleperz/fe3a0eb4eda888221229730e34b28b89

Against 100+ hosts.
