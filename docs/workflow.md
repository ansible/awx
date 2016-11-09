## Tower Workflow Overview
Workflows are structured pipelines of multiple tower job runs. Think of workflows as jobs that have no native content, but triggers other job in specific orders to accomplish the purpose of tracking the full set of jobs that were part of a release process as a single unit.

A workflow job is composed of one or more decision trees, each node of which wraps around zero to one tower job. A workflow job run starts with creating and running jobs of the root node of each decision tree. When a parent node has its job finished running, it would pick up a subset of its child nodes according to its job status, and create new jobs for them. The selected child nodes would then run their own jobs and so forth till all nodes that needs to run finish running, which marks the end of the underlying workflow run.

## Usage Manual

### Workflow CUID
Like other job resources, workflow jobs are created based on workflow job templates. Workflow job templates are equipped with common funtional fields including labels, schedules, notification templates, extra variables and survey specifications. It also comes with a custom `workflow_nodes` field which refers to a list of related workflow job template nodes.

The CUID operations against a workflow job template and its corresponding workflow jobs are almost identical to those of normal job templates and related jobs. However, from RBAC perspective, CUID on workflow job templates/jobs are limited to administrators. That is, an organization administrator takes full control over all workflow job templates/jobs under the same organization, while an organization auditor is able to see workflow job templates/jobs under the same organization. On the other hand, ordinary organization members have no, and are not able to gain, permission over any workflow-related resources.

### Workflow Nodes
Workflow Nodes are containers of workflow spawned jobs and function as nodes of workflow decision trees. Like that of workflow itself, the two types of workflow nodes are workflow job template nodes and workflow job nodes. 

Workflow job template nodes are listed and created under endpoint `/workflow_job_templates/\d/workflow_nodes/` to be associated with underlying workflow job template, or under endpoint `/workflow_job_template_nodes/` directly. The most important fields of a workflow job template node are `success_nodes`, `failure_nodes`, `always_nodes`, `unified_job_template` and `workflow_job_template`. The former three are lists of workflow job template nodes that in union forms the set of all it s child nodes, in specific, `success_nodes` are triggered when parnent node job succeeds, `failure_nodes` are triggered when parent node job fails, and `always_nodes` are triggered regardless of whether parent job fails. The later two reference the job template resource it contains and workflow job template it belongs to.

Workflow job nodes are created by workflow job template nodes at the beginning of workflow job run. Other than the fields inherited from its template, workflow job nodes also come with a `job` field which references the to-be-spawned job resource.

### Decision Tree Formation and Restrictions
The decision tree structure of a workflow is enforced by associating workflow job template nodes via endpoints `/workflow_job_template_nodes/\d/*_nodes/`, where `*` has options `success`, `failure` and `always`. However there are restrictions that must be enforced when setting up new connections. Here are the three restrictions that will raise validation error when break:
* Cycle restriction: According to decision tree definition, no cycle is allowed.
* Convergent restriction: Different paths should not come into the same node, in other words, a node cannot have multiple parents.
* Mutex restriction: A node cannot have all three types of child nodes. It contains either always nodes only, or any type other than always nodes.

### Workflow Run Details
A typical workflow run starts by either POSTing to endpoint `/workflow_job_templates/7/launch/`, or being triggered automatically by related schedule. The first step is the workflow job template creating workflow job, and all related workflow job template nodes creating workflow job node. Right after that, all root nodes are populated with corresponding job resources and start running. If nothing goes wrong, each decision tree will follow its own route to completion. The entire workflow finishes running when all its decision trees completes.

Job resources spawned by workflow jobs are needed by workflow to run correctly. Therefore deletion of spawned job resources is blocked while the underlying workflow job is executing.

Other than success and failure, a workflow spawned job resource can also end with status 'error' and 'canceled'. When a workflow spawned job resource errors, all branches starting from that job will stop executing while the rest keep their own paces. Canceling a workflow spawned job resource follows the same path.

A workflow job itself can also be canceled altogether. In this case all its spawned job resources will be canceled and following paths stop executing.

Like job templates, workflow job templates can associated with notification templates and notifications works exactly the same as that of job templates. One distinction is the notification message body. Workflow jobs sends notification that contains not only the status of itself, but also status of all its spawned jobs. Typical notification body looks like this:
```
Workflow job summary:

- node #141 spawns no job.
- node #139 spawns job #212, "foo", which finished with status successful.
- node #140 spawns job #213, "bar", which finished with status failed.
...
```

## Acceptance Criteria

## Testing Considerations

## Performance Testing
