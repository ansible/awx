# Start Job

Make a GET request to this resource to determine if the job can be started and
whether any passwords are required to start the job.  The response will include
the following fields:

* `can_start`: Flag indicating if this job can be started (boolean, read-only)
* `passwords_needed_to_start`: Password names required to start the job (array,
  read-only)

Make a POST request to this resource to start the job.  If any passwords are
required, they must be passed via POST data.

If successful, the response status code will be 202.  If any required passwords
are not provided, a 400 status code will be returned.  If the job cannot be
started, a 405 status code will be returned.
