# Workflow Job Template Workflow Node List

Workflow nodes reference templates to execute and define the ordering
in which to execute them. After a job in this workflow finishes,
the subsequent actions are to:

 - run nodes contained in "failure_nodes" or "always_nodes" if job failed
 - run nodes contained in "success_nodes" or "always_nodes" if job succeeded

The workflow is marked as failed if any jobs run as part of that workflow fail
and have the field `fail_on_job_failure` set to true. If not, the workflow
job is marked as successful.

{% include "api/sub_list_create_api_view.md" %}