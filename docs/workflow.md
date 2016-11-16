## Tower Workflow Overview
Workflows are structured compositions of Tower job resources. The only job of a workflow is to trigger other jobs in specific orders to achieve certain goals, such as tracking the full set of jobs that were part of a release process as a single unit.

A workflow has an associated tree-graph that is composed of multiple nodes. Each node in the tree has one associated job template (job template, inventory update, or project update) along with related resources that, if defined, will override the associated job template resources (i.e. credential, inventory, etc.) if the job template associated with the node is chosen to run.

## Usage Manual

### Workflow Create-Read-Update-Delete (CRUD)
Like other job resources, workflow jobs are created from workflow job templates. The API exposes common fields similar to job templates, including labels, schedules, notification templates, extra variables and survey specifications. Other than that, in the API, the related workflow graph nodes can be gotten to via the related workflow_nodes field.

The CRUD operations against a workflow job template and its corresponding workflow jobs are almost identical to those of normal job templates and related jobs. However, from an RBAC perspective, CRUD on workflow job templates/jobs are limited to super users. That is, an organization administrator takes full control over all workflow job templates/jobs under the same organization, while an organization auditor is able to see workflow job templates/jobs under the same organization. On the other hand, ordinary organization members have no, and are not able to gain, permission over any workflow-related resources.

### Workflow Nodes
Workflow Nodes are containers of workflow spawned job resources and function as nodes of workflow decision trees. Like that of workflow itself, the two types of workflow nodes are workflow job template nodes and workflow job nodes. 

Workflow job template nodes are listed and created under endpoint `/workflow_job_templates/\d+/workflow_nodes/` to be associated with underlying workflow job template, or directly under endpoint `/workflow_job_template_nodes/`. The most important fields of a workflow job template node are `success_nodes`, `failure_nodes`, `always_nodes`, `unified_job_template` and `workflow_job_template`. The former three are lists of workflow job template nodes that, in union, forms the set of all its child nodes, in specific, `success_nodes` are triggered when parnent node job succeeds, `failure_nodes` are triggered when parent node job fails, and `always_nodes` are triggered regardless of whether parent job succeeds or fails; The later two reference the job template resource it contains and workflow job template it belongs to.

Apart from the core fields, workflow job template nodes have optional fields `credential`, `inventory` and `char_prompts`. These fields will be passed on to corresponding fields of underlying jobs if those fields are set prompted at runtime.

When a workflow job template is launched a workflow job is created. A workflow job node is create for each WFJT node and all fields from the WFJT node are copied. Note that workflow job nodes contain all fields that a workflow job template node contains plus an additional `job` field, which is a reference to the to-be-spawned job resource.

### Tree-Graph Formation and Restrictions
The tree-graph structure of a workflow is enforced by associating workflow job template nodes via endpoints `/workflow_job_template_nodes/\d+/*_nodes/`, where `*` has options `success`, `failure` and `always`. However there are restrictions that must be enforced when setting up new connections. Here are the three restrictions that will raise validation error when break:
* Cycle restriction: According to tree definition, no cycle is allowed.
* Convergent restriction: Different paths should not come into the same node, in other words, a node cannot have multiple parents.
* Mutex restriction: A node cannot have all three types of child nodes. It contains either always nodes only, or any type other than always nodes.

### Workflow Run Details
A typical workflow run starts by either POSTing to endpoint `/workflow_job_templates/\d+/launch/`, or being triggered automatically by related schedule. At the very first, the workflow job template creats workflow job, and all related workflow job template nodes create workflow job nodes. Right after that, all root nodes are populated with corresponding job resources and start running. If nothing goes wrong, each decision tree will follow its own route to completion. The entire workflow finishes running when all its decision trees complete.

Job resources spawned by workflow jobs are needed by workflow to run correctly. Therefore deletion of spawned job resources is blocked while the underlying workflow job is executing.

Other than success and failure, a workflow spawned job resource can also end with status 'error' and 'canceled'. When a workflow spawned job resource errors, all branches starting from that job will stop executing while the rest keep their own paces. Canceling a workflow spawned job resource follows the same rules.

A workflow job itself can also be canceled. In this case all its spawned job resources will be canceled if cancelable and following paths stop executing.

Like job templates, workflow job templates can be associated with notification templates and notifications work exactly the same as that of job templates. One distinction is the notification message body. Workflow jobs sends notification body that contains not only the status of itself, but also status of all its spawned jobs. A typical notification body looks like this:
```
Workflow job summary:

- node #141 spawns no job.
- node #139 spawns job #212, "foo", which finished with status successful.
- node #140 spawns job #213, "bar", which finished with status failed.
...
```

### Workflow Copy and Relaunch
Other than the normal way of creating workflow job templates/jobs, it is also possible to copy existing workflow job templates/jobs. The resulting new workflow job resource will be almost identical to which it copies from, with several unique fields to identify itself as well as to indicate its copy nature.

Workflow job templates can be copied by POSTing to endpoint `/workflow_job_templates/\d+/copy/`. After copy finished, the resulting new workflow job template will have identical fields including description, extra_vars, labels, 'launch_type' and survey-related fields (survey_passwords, survey_spec and survey_enabled). More importantly, all workflow job template nodes of the original workflow job template, as well as the topology they bear, will be copied. On the other hand, schedules and notification templates of the original workflow job template will not be copied nor shared, and the name of the created workflow job template is the original name plus a special-formatted suffix to indicate its copy origin, such as **TODO**.

Worflow jobs cannot be copied directly, instead a workflow job is implicitly copied when it needs to relaunch. Relaunching an existing workflow job is done by POSTing to endpoint `/workflow_jobs/\d+/relaunch/`. What happens next is the original workflow job is copied to create a new workflow job. The new workflow job then gets a copy of all nodes of the original as well as the topology they bear. Finally the full-fledged new workflow job is triggered to run, thus fulfilling the purpose of relaunch.

## Test Coverage
### CRUD-related
* Verify that CRUD operations on all workflow resources are working properly. Note workflow job nodes cannot be created or deleted independently, but verifications are needed to make sure when a workflow job is deleted, all its related workflow job nodes are deleted.
* Verify the RBAC property of workflow resources. In specific: 
  * Workflow job templates can only be accessible by superusers ---- system admin, admin of the same organization and system auditor and auditor of the same organization with read permission only.
  * Workflow jobs follows the permission rules of its associated workflow job template.
  * Workflow job template nodes rely their permission rules on the permission rules of both their associated workflow job template and unified job template.
  * Workflow job nodes follows the permission rules of both its associated workflow job and unified job.
* Verify that workflow job template nodes can be created under, or (dis)associated with workflow job templates.
* Verify that only the permitted types of job template types can be associated with a workflow job template node. Currently the permitted types are *job templates, inventory sources and projects*.
* Verify that workflow job template nodes under the same workflow job template can be associated to form parent-child relationship of decision trees. In specific, one node takes another as its child node by POSTing another node's id to one of the three endpoints: `/success_nodes/`, `/failure_nodes/` and `/always_nodes/`.
* Verify that workflow job template nodes are not allowed to have invalid association. Any attempt that causes invalidity will trigger 400-level response. The three types of invalid associations are cycle, convergence(multiple parent) and mutex('always' XOR the rest).
* Verify that a workflow job template can be successfully copied and the created workflow job template does not miss any field that should be copied or intentionally modified.

### Task-related
* Verify that workflow jobs can be launched by POSTing to endpoint `/workflow_job_templates/\d/launch/`.
* Verify that schedules can be successfully (dis)associated with a workflow job template, and workflow jobs can be triggered by the schedule of associated workflow job template at specified time point.
* Verify that extra variables and surveys work for workflow job templates the same way as they work for normal job templates.
* Verify that during a workflow job run, all its decision trees follow their correct paths of execution. Unwarranted behaviors include child node executing before its parent and wrong path being selected (*failure nodes* are executed when parent node *succeeds* and so on).
* Verify that a subtree of execution will never start if its root node runs into internal error (*not ends with failure*).
* Verify that a subtree of execution will never start if its root node is successfully canceled.
* Verify that cancelling a workflow job that is cancellable will consequently cancel any of its cancellable spawned jobs and thus interrupts the whole workflow execution.
* Verify that during a workflow job run, deleting its spawned jobs are prohibited.
* Verify that at the beginning of each spawned job run, its prompted fields will be populated by the wrapping workflow job node with corrected values. For example, `credential` field of workflow job node goes to `credential` field of spawned job.
* Verify that notification templates can be successfully (dis)associated with a workflow job template. Later when its spawned workflow jobs finish running, verify that the correct type of notifications will be sent according to the job status.
* Verify that a workflow job can be successfully relaunched.

## Test Notes
* Please apply non-trivial topology when testing workflow run. A non-trivial topology for a workflow job template should include:
  * Multiple decision trees.
  * Relatively large hight in each decision tree.
  * All three types of relationships (`success`, `failure` and `always`).
