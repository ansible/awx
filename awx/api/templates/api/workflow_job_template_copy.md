Copy a Workflow Job Template:

Make a GET request to this resource to determine if the workflow_job_template
can be copied and whether any passwords are required to launch the
workflow_job_template. The response will include the following fields:

* `can_copy`: Flag indicating whether the active user has permission to make
  a copy of this workflow_job_template, provides same content as the
  workflow_job_template detail view summary_fields.user_capabilities.copy
  (boolean, read-only)
* `can_copy_without_user_input`: Flag indicating if the user should be
  prompted for confirmation before the copy is executed (boolean, read-only)
* `templates_unable_to_copy`: Names of job templates, projects, and inventory
  sources that the active user lacks permission to use and will be missing in
  workflow nodes of the copy (array, read-only)
* `inventories_unable_to_copy`: Names of inventories that the active user
  lacks permission to use and will be missing in the workflow nodes of the
  copy (array, read-only)
* `credentials_unable_to_copy`: Names of credentials that the active user
  lacks permission to use and will be missing in the workflow nodes of the
  copy (array, read-only)

Make a POST request to this endpoint to save a copy of this
workflow_job_template. No POST data is accepted for this action.

If successful, the response status code will be 201. The response body will
contain serialized data about the new workflow_job_template, which will be
similar to the original workflow_job_template, but with an additional `@`
and a timestamp in the name.

All workflow nodes and connections in the original will also exist in the
copy. The nodes will be missing related resources if the user did not have
access to use them.
