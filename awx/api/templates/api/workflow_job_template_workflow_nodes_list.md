# Workflow Job Template Workflow Node List

Workflow nodes reference templates to execute and define the ordering
in which to execute them. After a job ran as part of a workflow finishes
the subsequent actions will be to.

 - run nodes contained in "failure_nodes" or "always_nodes" if job failed
 - run nodes contained in "success_nodes" or "always_nodes" if job succeeded

The workflow will be marked as failed if any jobs ran as a part of the workflow
fail and have the field `fail_on_job_failure` set to true. If not, the
workflow job will be marked as successful.

{% include "api/sub_list_create_api_view.md" %}