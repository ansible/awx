Launch a Job Template:

Make a POST request to this resource to launch the system job template.

Variables specified inside of the parameter `extra_vars` are passed to the
system job task as command line parameters. These tasks can be run manually
on the host system via the `awx-manage` command.

For example on `cleanup_jobs` and `cleanup_activitystream`:

`{"extra_vars": {"days": 30}}`

Which will act on data older than 30 days.

For `cleanup_activitystream` and `cleanup_jobs` commands, providing
`"dry_run": true` inside of `extra_vars` will show items that will be
removed without deleting them.

Specific resources can be optionally listed for `cleanup_jobs` by sending
an array named "resources" containing the resources to be cleaned.  For
example.

`{"extra_vars": {"resources":["notifications", "project-updates"]}}`

The resources correspond to the available "awx-manage cleanup" arguments
and are listed below.

"jobs", "project-updates", "inventory-updates","management-jobs",
 "ad-hoc-commands", "workflow-jobs", "notifications"

If "resources" is omitted, all resources are cleaned up.


Each individual system job task has its own default values, which are
applicable either when running it from the command line or launching its
system job template with empty `extra_vars`.

 - Defaults for `cleanup_activitystream`: days=90
 - Defaults for `cleanup_jobs`: days=90

If successful, the response status code will be 202.  If the job cannot be
launched, a 405 status code will be returned.
