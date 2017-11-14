Launch a Job Template:

Make a GET request to this resource to determine if the job_template can be
launched and whether any passwords are required to launch the job_template.
The response will include the following fields:

* `ask_variables_on_launch`: Flag indicating whether the job_template is
  configured to prompt for variables upon launch (boolean, read-only)
* `ask_tags_on_launch`: Flag indicating whether the job_template is
  configured to prompt for tags upon launch (boolean, read-only)
* `ask_skip_tags_on_launch`: Flag indicating whether the job_template is
  configured to prompt for skip_tags upon launch (boolean, read-only)
* `ask_job_type_on_launch`: Flag indicating whether the job_template is
  configured to prompt for job_type upon launch (boolean, read-only)
* `ask_limit_on_launch`: Flag indicating whether the job_template is
  configured to prompt for limit upon launch (boolean, read-only)
* `ask_inventory_on_launch`: Flag indicating whether the job_template is
  configured to prompt for inventory upon launch (boolean, read-only)
* `ask_credential_on_launch`: Flag indicating whether the job_template is
  configured to prompt for credential upon launch (boolean, read-only)
* `can_start_without_user_input`: Flag indicating if the job_template can be
  launched without user-input (boolean, read-only)
* `passwords_needed_to_start`: Password names required to launch the
  job_template (array, read-only)
* `variables_needed_to_start`: Required variable names required to launch the
  job_template (array, read-only)
* `survey_enabled`: Flag indicating whether the job_template has an enabled
  survey (boolean, read-only)
* `inventory_needed_to_start`: Flag indicating the presence of an inventory
  associated with the job template.  If not then one should be supplied when
  launching the job (boolean, read-only)

Make a POST request to this resource to launch the job_template. If any
passwords, inventory, or extra variables (extra_vars) are required, they must
be passed via POST data, with extra_vars given as a YAML or JSON string and
escaped parentheses. If the `inventory_needed_to_start` is `True` then the
`inventory` is required.

If successful, the response status code will be 201.  If any required passwords
are not provided, a 400 status code will be returned.  If the job cannot be
launched, a 405 status code will be returned. If the provided credential or
inventory are not allowed to be used by the user, then a 403 status code will
be returned.
