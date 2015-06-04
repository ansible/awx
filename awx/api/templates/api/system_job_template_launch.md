Launch a Job Template:

Make a POST request to this resource to launch the system job template.

An extra parameter `extra_vars` is suggested in order to pass extra parameters
to the system job task.

For example on `cleanup_jobs`, `cleanup_deleted`, and `cleanup_activitystream`:

`{"days": 30}`

Which will act on data older than 30 days.

For `cleanup_facts`:

`{"older_than": "4w", `granularity`: "3d"}`

Which will reduce the granularity of scan data to one scan per 3 days when the data is older than 4w.

If successful, the response status code will be 202.  If the job cannot be
launched, a 405 status code will be returned.
