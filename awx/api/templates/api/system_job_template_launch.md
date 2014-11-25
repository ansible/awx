Launch a Job Template:

Make a POST request to this resource to launch the system job template.

An extra parameter `extra_vars` is suggested in order to pass extra parameters
to the system job task.  For example:   `{"days": 30}` to perform the action on
items older than 30 days.

If successful, the response status code will be 202.  If the job cannot be
launched, a 405 status code will be returned.
