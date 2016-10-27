# Workflow Job Template Workflow Node List

Workflow nodes reference templates to execute and define the ordering
in which to execute them. After a job in this workflow finishes,
the subsequent actions are to:

 - run nodes contained in "failure_nodes" or "always_nodes" if job failed
 - run nodes contained in "success_nodes" or "always_nodes" if job succeeded

The workflow job is marked as `successful` if all of the jobs running as
a part of the workflow job have completed, and the workflow job has not
been canceled. Even if a job within the workflow has failed, the workflow
job will not be marked as failed.

{% include "api/sub_list_create_api_view.md" %}