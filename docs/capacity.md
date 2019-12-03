## Ansible Tower Capacity Determination and Job Impact

The Ansible Tower capacity system determines how many jobs can run on an Instance given the amount of resources
available to the Instance and the size of the jobs that are running (referred to hereafter as `Impact`).
The algorithm used to determine this is based entirely on two things:

* How much memory is available to the system (`mem_capacity`)
* How much CPU is available to the system (`cpu_capacity`)

Capacity also impacts Instance Groups. Since Groups are composed of Instances, likewise Instances can be
assigned to multiple Groups. This means that impact to one Instance can potentially affect the overall capacity of
other Groups.

Instance Groups (not Instances themselves) can be assigned to be used by Jobs at various levels (see [Tower Clustering/HA Overview](https://github.com/ansible/awx/blob/devel/docs/clustering.md)).
When the Task Manager is preparing its graph to determine which Group a Job will run on, it will commit the capacity of
an Instance Group to a Job that hasn't or isn't ready to start yet (see [Task Manager Overview](https://github.com/ansible/awx/blob/devel/docs/task_manager_system.md)).

Finally, if only one Instance is available (especially in smaller configurations) for a Job to run, the Task Manager will allow that
Job to run on the Instance even if it would push the Instance over capacity. We do this as a way to guarantee that jobs
themselves won't get clogged as a result of an under-provisioned system.

These concepts mean that, in general, Capacity and Impact is not a zero-sum system relative to Jobs and Instances/Instance Groups.


### Resource Determination For Capacity Algorithm

The capacity algorithms are defined in order to determine how many `forks` a system is capable of running at the same time. This controls how
many systems Ansible itself will communicate with simultaneously. Increasing the number of forks a Tower system is running will, in general,
allow jobs to run faster by performing more work in parallel. The tradeoff is that this will increase the load on the system which could cause work
to slow down overall.

Tower can operate in two modes when determining capacity. `mem_capacity` (the default) will allow you to overcommit CPU resources while protecting the system
from running out of memory. If most of your work is not CPU-bound, then selecting this mode will maximize the number of forks.


#### Memory Relative Capacity
`mem_capacity` is calculated relative to the amount of memory needed per-fork. Taking into account the overhead for Tower's internal components, this comes out
to be about `100MB` per fork. When considering the amount of memory available to Ansible jobs the capacity algorithm will reserve 2GB of memory to account
for the presence of other Tower services. The algorithm itself looks like this:

    (mem - 2048) / mem_per_fork

As an example:

    (4096 - 2048) / 100 == ~20

So a system with 4GB of memory would be capable of running 20 forks. The value `mem_per_fork` can be controlled by setting the Tower settings value
(or environment variable) `SYSTEM_TASK_FORKS_MEM` which defaults to `100`.


#### CPU-Relative Capacity

Often times Ansible workloads can be fairly CPU-bound. In these cases, sometimes reducing the simultaneous workload allows more tasks to run faster and reduces
the average time-to-completion of those jobs.

Just as the Tower `mem_capacity` algorithm uses the amount of memory needed per-fork, the `cpu_capacity` algorithm looks at the amount of CPU resources is needed
per fork. The baseline value for this is `4` forks per core. The algorithm itself looks like this:

    cpus * fork_per_cpu

For example, in a 4-core system:

    4 * 4 == 16

The value `fork_per_cpu` can be controlled by setting the Tower settings value (or environment variable) `SYSTEM_TASK_FORKS_CPU`, which defaults to `4`.

### Job Impacts Relative To Capacity

When selecting the capacity, it's important to understand how each job type affects it.

It's helpful to understand what `forks` mean to Ansible: http://docs.ansible.com/ansible/latest/intro_configuration.html#forks

The default forks value for ansible is `5`. However, if Tower knows that you're running against fewer systems than that, then the actual concurrency value
will be lower.

When a job is made to run, Tower will add `1` to the number of forks selected to compensate for the Ansible parent process. So if you are running a playbook against `5`
systems with a `forks` value of `5`, then the actual `forks` value from the perspective of Job Impact will be 6.

#### Impact of Job Types in Tower

Jobs and Ad-hoc jobs follow the above model, `forks + 1`.

Other job types have a fixed impact:

* Inventory Updates: 1
* Project Updates: 1
* System Jobs: 5

### Selecting the Right Capacity

Selecting between a memory-focused capacity algorithm and a CPU-focused capacity for your Tower use means you'll be selecting between a minimum
and maximum value. In the above examples, the CPU capacity would allow a maximum of 16 forks while the Memory capacity would allow 20. For some systems,
the disparity between these can be large and oftentimes you may want to have a balance between these two.

An Instance field, `capacity_adjustment`, allows you to select how much of one or the other you want to consider. It is represented as a value between `0.0`
and `1.0`.  If set to a value of `1.0`, then the largest value will be used. In the above example, that would be Memory capacity, so a value of `20` forks would
be selected. If set to a value of `0.0` then the smallest value will be used. A value of `0.5` would be a 50/50 balance between the two algorithms which would
be `18`:

    16 + (20 - 16) * 0.5 == 18
