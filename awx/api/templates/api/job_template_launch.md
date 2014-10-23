Launch a Job Template:

Make a GET request to this resource to determine if the job_template can be
launched and whether any passwords are required to launch the job_template.
The response will include the following fields:

* `ask_variables_on_launch`: Flag indicating whether the job_template is
  configured to prompt for variables upon launch (boolean, read-only)
* `can_start_without_user_input`: Flag indicating if the job_template can be
  launched without user-input (boolean, read-only)
* `passwords_needed_to_start`: Password names required to launch the
  job_template (array, read-only)
* `variables_needed_to_start`: Required variable names required to launch the
  job_template (array, read-only)
* `survey_enabled`: Flag indicating if whether the job_template has an enabled
  survey (boolean, read-only)

Make a POST request to this resource to launch the job_template.  If any
passwords or variables are required, they must be passed via POST data.

If successful, the response status code will be 202.  If any required passwords
are not provided, a 400 status code will be returned.  If the job cannot be
launched, a 405 status code will be returned.
