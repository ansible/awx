## AWX Capacity Determination and Job Impact

The AWX capacity system determines how many jobs can run on an Instance given the amount of resources
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
many systems Ansible itself will communicate with simultaneously. Increasing the number of forks a AWX system is running will, in general,
allow jobs to run faster by performing more work in parallel. The tradeoff is that this will increase the load on the system which could cause work
to slow down overall.

AWX can operate in two modes when determining capacity. `mem_capacity` (the default) will allow you to overcommit CPU resources while protecting the system
from running out of memory. If most of your work is not CPU-bound, then selecting this mode will maximize the number of forks.


#### Memory Relative Capacity
`mem_capacity` is calculated relative to the amount of memory needed per-fork. Taking into account the overhead for AWX's internal components, this comes out
to be about `100MB` per fork. When considering the amount of memory available to Ansible jobs the capacity algorithm will reserve 2GB of memory to account
for the presence of other AWX services. The algorithm itself looks like this:

    (mem - 2048) / mem_per_fork

As an example:

    (4096 - 2048) / 100 == ~20

So a system with 4GB of memory would be capable of running 20 forks. The value `mem_per_fork` can be controlled by setting the AWX settings value
(or environment variable) `SYSTEM_TASK_FORKS_MEM` which defaults to `100`.


#### CPU-Relative Capacity

Often times Ansible workloads can be fairly CPU-bound. In these cases, sometimes reducing the simultaneous workload allows more tasks to run faster and reduces
the average time-to-completion of those jobs.

Just as the AWX `mem_capacity` algorithm uses the amount of memory needed per-fork, the `cpu_capacity` algorithm looks at the amount of CPU resources is needed
per fork. The baseline value for this is `4` forks per core. The algorithm itself looks like this:

    cpus * fork_per_cpu

For example, in a 4-core system:

    4 * 4 == 16

The value `fork_per_cpu` can be controlled by setting the AWX settings value (or environment variable) `SYSTEM_TASK_FORKS_CPU`, which defaults to `4`.

### Job Impacts Relative To Capacity

When selecting the capacity, it's important to understand how each job type affects it.

It's helpful to understand what `forks` mean to Ansible: http://docs.ansible.com/ansible/latest/intro_configuration.html#forks

The default forks value for ansible is `5`. However, if AWX knows that you're running against fewer systems than that, then the actual concurrency value
will be lower.

When a job is made to run, AWX will add `1` to the number of forks selected to compensate for the Ansible parent process. So if you are running a playbook against `5`
systems with a `forks` value of `5`, then the actual `forks` value from the perspective of Job Impact will be 6.

#### Impact of Job Types in AWX
Jobs have two types of impact. Task "execution" impact and task "control" impact.

For instances that are the "controller_node" for a task,
the impact is set by settings.AWX_CONTROL_NODE_TASK_IMPACT and it is the same no matter what type of job.

For instances that are the "execution_node" for a task, the impact is calculated as following:

Jobs and Ad-hoc jobs follow the above model, `forks + 1`.

Other job types have a fixed execution impact:

* Inventory Updates: 1
* Project Updates: 1
* System Jobs: 5

For jobs that execute on the same node as they are controlled by, both settings.AWX_CONTROL_NODE_TASK_IMPACT and the job task execution impact apply.

Examples:
Given settings.AWX_CONTROL_NODE_TASK_IMPACT is 1:
  - Project updates (where the execution_node is always the same as the controller_node), have a total impact of 2.
  - Container group jobs (where the execution node is not a member of the cluster) only control impact applies, and the controller node has a total task impact of 1.
  - A job executing on a "hybrid" node where both control and execution will occur on the same node has the task impact of (1 overhead for ansible main process) + (min(forks,hosts)) + (1 control node task impact). Meaning a Job running on a hybrid node with forks set to 1 would have a total task impact of 3.

### Selecting the Right settings.AWX_CONTROL_NODE_TASK_IMPACT

This setting allows you to determine how much impact controlling jobs has. This
can be helpful if you notice symptoms of your control plane exceeding desired
CPU or memory usage, as it effectively throttles how many jobs can be run
concurrently by your control plane. This is usually a concern with container
groups, which at this time effectively have infinite capacity, so it is easy to
end up with too many jobs running concurrently, overwhelming the control plane
pods with events and control processes.

If you want more throttling behavior, increase the setting.
If you want less throttling behavior, lower the setting.

### Selecting the Right Capacity

Selecting between a memory-focused capacity algorithm and a CPU-focused capacity for your AWX use means you'll be selecting between a minimum
and maximum value. In the above examples, the CPU capacity would allow a maximum of 16 forks while the Memory capacity would allow 20. For some systems,
the disparity between these can be large and oftentimes you may want to have a balance between these two.

An Instance field, `capacity_adjustment`, allows you to select how much of one or the other you want to consider. It is represented as a value between `0.0`
and `1.0`.  If set to a value of `1.0`, then the largest value will be used. In the above example, that would be Memory capacity, so a value of `20` forks would
be selected. If set to a value of `0.0` then the smallest value will be used. A value of `0.5` would be a 50/50 balance between the two algorithms which would
be `18`:

    16 + (20 - 16) * 0.5 == 18

### Max forks and Max Concurrent jobs on Instance Groups and Container Groups

By default, only Instances have capacity and we only track capacity consumed per instance. With the max_forks and max_concurrent_jobs fields now available on Instance Groups, we additionally can limit how many jobs or forks are allowed to be concurrently consumed across an entire Instance Group or Container Group.

This is especially useful for Container Groups where previously, there was no limit to how many jobs we would submit to a Container Group, which made it impossible to "overflow" job loads from one Container Group to another container group, which may be on a different Kubernetes cluster or namespace.

One way to calculate what max_concurrent_jobs is desirable to set on a Container Group is to consider the pod_spec for that container group. In the pod_spec we indicate the resource requests and limits for the automation job pod. If you pod_spec indicates that a pod with 100MB of memory will be provisioned, and you know your Kubernetes cluster has 1 worker node with 8GB of RAM, you know that the maximum number of jobs that you would ideally start would be around 81 jobs, calculated by taking  (8GB memory on node * 1024 MB) // 100 MB memory/job pod which with floor division comes out to 81.

Alternatively, instead of considering the number of job pods and the resources requested, we can consider the memory consumption of the forks in the jobs. We normally consider that 100MB of memory will be used by each fork of ansible. Therefore we also know that our 8 GB worker node should also only run 81 forks of ansible at a time -- which depending on the forks and inventory settings of the job templates, could be consumed by anywhere from 1 job to 81 jobs. So we can also set max_forks = 81. This way, either 39 jobs with 1 fork can run (task impact is always forks + 1), or 2 jobs with forks set to 39 can run.

While this feature is most useful for Container Groups where there is no other way to limit job execution, this feature is available for use on any instance group. This can be useful if for other business reasons you want to set a InstanceGroup wide limit on concurrent jobs. For example, if you have a job template that you only want 10 copies of running at a time -- you could create a dedicated instance group for that job template and set max_concurrent_jobs to 10.
