Launch a Job Template:

Make a POST request to this resource to launch the system job template.

Variables specified inside of the parameter `extra_vars` are passed to the
system job task as command line parameters. These tasks can be ran manually
on the host system via the `tower-manage` command.

For example on `cleanup_jobs` and `cleanup_activitystream`:

`{"days": 30}`

Which will act on data older than 30 days.

For `cleanup_facts`:

`{"older_than": "4w", "granularity": "3d"}`

Which will reduce the granularity of scan data to one scan per 3 days when the data is older than 4w.

Each individual system job task has its own default values, which are
applicable either when running it from the command line or launching its
system job template with empty `extra_vars`.

 - Defaults for `cleanup_activitystream`: days=90
 - Defaults for `cleanup_facts`: older_than="30d", granularity="1w"
 - Defaults for `cleanup_jobs`: days=90

If successful, the response status code will be 202.  If the job cannot be
launched, a 405 status code will be returned.
