Launch a Workflow Job Template:

Make a GET request to this resource to determine if the workflow_job_template
can be launched and whether any passwords are required to launch the
workflow_job_template. The response will include the following fields:

* `can_start_without_user_input`: Flag indicating if the workflow_job_template
  can be launched without user-input (boolean, read-only)
* `variables_needed_to_start`: Required variable names required to launch the
  workflow_job_template (array, read-only)
* `survey_enabled`: Flag indicating whether the workflow_job_template has an
  enabled survey (boolean, read-only)
* `extra_vars`: Text which is the `extra_vars` field of this workflow_job_template
  (text, read-only)
* `node_templates_missing`: List of node ids of all nodes that have a
  null `unified_job_template`, which will cause their branches to stop
  execution (list, read-only)
* `node_prompts_rejected`: List of node ids of all nodes that have
  specified a field that will be rejected because its  `unified_job_template`
  does not allow prompting for this field, this will not halt execution of
  the branch but the field will be ignored (list, read-only)
* `workflow_job_template_data`: JSON object listing general information of
  this workflow_job_template (JSON object, read-only)

Make a POST request to this resource to launch the workflow_job_template. If any
credential, inventory, project or extra variables (extra_vars) are required, they
must be passed via POST data, with extra_vars given as a YAML or JSON string and
escaped parentheses.

If successful, the response status code will be 201.  If any required passwords
are not provided, a 400 status code will be returned.  If the workflow job cannot
be launched, a 405 status code will be returned. If the provided credential or
inventory are not allowed to be used by the user, then a 403 status code will
be returned.
