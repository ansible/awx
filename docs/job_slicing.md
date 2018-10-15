# Job Slicing Overview

Ansible, by default, runs jobs from a single control instance. At best a single Ansible job can be sliced up on a single system via forks but this doesn't fully take advantage of AWX's ability to distribute work to multiple nodes in a cluster.

Job Slicing solves this by adding a Job Template field `job_slice_count`. This field specifies the number of **Jobs** to slice the Ansible run into. When this number is greater than 1 ``AWX`` will generate a **Workflow** from a **JobTemplate** instead of a **Job**. The **Inventory** will be distributed evenly amongst the slice jobs. The workflow job is then started and proceeds as though it were a normal workflow.  The API will return either a **Job** resource (if `job_slice_count` < 2) or a **WorkflowJob** resource otherwise. Likewise, the UI will redirect to the appropriate screen to display the status of the run.

## Implications for Job execution

When jobs are sliced they can run on any Tower node and some may not run at the same time. Because of this, anything that relies on setting/sliced state (using modules such as ``set_fact``) will not work as expected. It's reasonable to expect that not all jobs will actually run at the same time (if there is not enough capacity in the system for example)

## Simultaneous Execution Behavior

By default Job Templates aren't normally configured to execute simultaneously (``allow_simultaneous`` must be checked). Slicing overrides this behavior and implies ``allow_simultaneous`` even if that setting is unchecked.
