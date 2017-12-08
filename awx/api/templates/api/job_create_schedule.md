Create a schedule based on a job:

Make a POST request to this endpoint to create a schedule that launches
the job template that launched this job, and uses the same
parameters that the job was launched with. These parameters include all
"prompted" resources such as `extra_vars`, `inventory`, `limit`, etc.

Jobs that were launched with user-provided passwords cannot have a schedule
created from them.

Make a GET request for information about what those prompts are and
whether or not a schedule can be created.
