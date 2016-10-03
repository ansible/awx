## Tower Clustering/HA Overview

Prior to 3.1 the Ansible Tower HA solution was not a true high-availability system. In 3.1 we have rewritten this system entirely with a new focus in mind:

* Each node should be able to act as an entrypoint for UI and API Access.
  This should enable Tower administrators to use load balancers in front of as many nodes as they wish
  and maintain good data visibility.
* Each node should be able to join the Tower cluster and expand its ability to execute jobs. This is currently
  a naive system where jobs can and will run anywhere rather than be directed on where to run. *That* work will
  be done later when building out the Federation/Rampart system.
* Provisioning new nodes should be as simple as updating the `inventory` file and re-running the setup playbook
* Nodes can be deprovisioned with a simple management commands

It's important to point out a few existing things:

* PostgreSQL is still a standalone instance node and is not clustered. We also won't manage replica configuration or,
  if the user configures standby replicas, database failover.
* All nodes should be reachable from all other nodes and they should be able to reach the database. It's also important
  for the hosts to have a stable address and/or hostname (depending on how you configure the Tower host)
* RabbitMQ is the cornerstone of Tower's Clustering system. A lot of our configuration requirements and behavior is dictated
  by its needs. Thus we are pretty inflexible to customization beyond what our setup playbook allows. Each Tower node has a
  deployment of RabbitMQ that will cluster with the other nodes' RabbitMQ instances.
* Existing old-style HA deployments will be transitioned automatically to the new HA system during the upgrade process.

## Important Changes

* There is no concept of primary/secondary in the new Tower system. *All* systems are primary.
* Setup playbook changes to configure rabbitmq and give hints to the type of network the hosts are on.
* The `inventory` file for Tower deployments should be saved/persisted. If new nodes are to be provisioned
  the passwords and configuration options as well as host names will need to be available to the installer.

## Concepts and Configuration

### Installation and the Inventory File
The current standalone node configuration doesn't change for a 3.1 deploy. The inventory file does change in some important ways:

* Since there is no primary/secondary configuration those inventory groups go away and are replaced with a
  single inventory group `tower`. The `database` group remains for specifying an external postgres, however:
  ```
  [tower]
  hostA
  hostB
  hostC
  
  [database]
  hostDB
  ```
* The `redis_password` field is removed from `[all:vars]`
* There are various new fields for RabbitMQ:
  - `rabbitmq_port=5672` - RabbitMQ is installed on each node and is not optional, it's also not possible to externalize. It is
    possible to configure what port it listens on and this setting controls that.
  - `rabbitmq_vhost=tower` - Tower configures a rabbitmq virtualhost to isolate itself. This controls that settings.
  - `rabbitmq_username=tower` and `rabbitmq_password=tower` - Each node will be configured with these values and each node's Tower
    instance will be configured with it also. This is similar to our other uses of usernames/passwords.
  - `rabbitmq_cookie=<somevalue>` - This value is unused in a standalone deployment but is critical for clustered deployments.
    This acts as the secret key that allows RabbitMQ cluster members to identify each other.
  - `rabbitmq_use_long_names` - RabbitMQ is pretty sensitive to what each node is named. We are flexible enough to allow FQDNs
    (host01.example.com), short names (host01), or ip addresses (192.168.5.73). Depending on what is used to identify each host
    in the `inventory` file this value may need to be changed. For FQDNs and ip addresses this value needs to be `true`. For short
    names it should be `false`
  - `rabbitmq_enable_manager` - Setting this to `true` will expose the RabbitMQ management web console on each node.

The most important field to point out for variability is `rabbitmq_use_long_name`. That's something we can't detect or provide a reasonable
default for so it's important to point out when it needs to be changed.

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

### Provisioning and Deprovisioning Nodes

* Provisioning
Provisioning Nodes after installation is supported by updating the `inventory` file and re-running the setup playbook. It's important that this file
contain all passwords and information used when installing the cluster or other nodes may be reconfigured (This could be intentional)

* Deprovisioning
Tower does not automatically de-provision nodes since we can't distinguish between a node that was taken offline intentionally or due to failure.
Instead the procedure for deprovisioning a node is to shut it down (or stop the `ansible-tower-service`) and run the Tower deprovision command:

```
$ tower-manage deprovision-node <nodename>
```

### Status and Monitoring

Tower itself reports as much status as it can via the api at `/api/v1/ping` in order to provide validation of the health
of the Cluster. This includes:

* The node servicing the HTTP request
* The last heartbeat time of all other nodes in the cluster
* The state of the Job Queue, any jobs each node is running
* The RabbitMQ cluster status

### Node Services and Failure Behavior

Each Tower node is made up of several different services working collaboratively:

* HTTP Services - This includes the Tower application itself as well as external web services.
* Callback Receiver - Whose job it is to receive job events from running Ansible jobs.
* Celery - The worker queue, that processes and runs all jobs.
* RabbitMQ - Message Broker, this is used as a signaling mechanism for Celery as well as any event data propogated to the application.
* Memcached - local caching service for the node it lives on.

Tower is configured in such a way that if any of these services or their components fail then all services are restarted. If these fail sufficiently
often in a short span of time then the entire node will be placed offline in an automated fashion in order to allow remediation without causing unexpected
behavior.

### Job Runtime Behavior

Ideally a regular user of Tower should not notice any semantic difference to the way jobs are run and reported. Behind the scenes its worth
pointing out the differences in how the system behaves.

When a job is submitted from the API interface it gets pushed into the Celery queue on RabbitMQ. A single RabbitMQ node is the responsible master for
individual queues but each Tower node will connect to and receive jobs from that queue using a Fair scheduling algorithm. Any node in the cluster is just
as likely to receive the work and execute the task. If a node fails while executing jobs then the work is marked as permanently failed.

As Tower nodes are brought online it effectively expands the work capacity of the Tower system which is measured as one entire unit (the cluster's capacity).
Conversely de-provisioning a node will remove capacity from the cluster.

It's important to note that not all nodes are required to be provisioned with an equal capacity.

Project updates behave differently than they did before. Previously they were ordinary jobs that ran on a single node. It's now important that
they run successfully on any node that could potentially run a job. Project updates will now fan out to all nodes in the cluster. Success or failure of
project updates will be conditional upon them succeeding on all nodes.

## Acceptance Criteria

When verifying acceptance we should ensure the following statements are true

* Tower should install as a standalone Node
* Tower should install in a Clustered fashion
* Provisioning should be supported via the setup playbook
* De-provisioning should be supported via a management command
* All jobs, inventory updates, and project updates should run successfully
* Jobs should be able to run on all hosts
* Project updates should manifest their data on all hosts simultaneously
* Tower should be able to reasonably survive the removal of all nodes in the cluster
* Tower should behave in a predictable fashiong during network partitioning

## Testing Considerations

* Basic testing should be able to demonstrate parity with a standalone node for all integration testing.
* We should test behavior of large and small clusters. I would envision small clusters as 2 - 3 nodes and large
  clusters as 10 - 15 nodes
* Failure testing should involve killing single nodes and killing multiple nodes while the cluster is performing work.
  Job failures during the time period should be predictable and not catastrophic.
* Node downtime testing should also include recoverability testing. Killing single services and ensuring the system can
  return itself to a working state
* Persistent failure should be tested by killing single services in such a way that the cluster node can not be recovered
  and ensuring that the node is properly taken offline
* Network partitioning failures will be important also. In order to test this
  - Disallow a single node from communicating with the other nodes but allow it to communicate with the database
  - Break the link between nodes such that it forms 2 or more groups where groupA and groupB can't communicate but all nodes
    can communicate with the database.
* Crucially when network partitioning is resolved all nodes should recover into a consistent state

## Performance Testing

Performance testing should be twofold.

* Large volume of simultaneous jobs.
* Jobs that generate a large amount of output.

These should also be benchmarked against the same playbooks using the 3.0.X Tower release and a stable Ansible version.
For a large volume playbook I might recommend a customer provided one that we've seen recently:

https://gist.github.com/michelleperz/fe3a0eb4eda888221229730e34b28b89

Against 100+ hosts.
