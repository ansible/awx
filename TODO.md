TODO items for ansible commander
================================

4/2 NOTES
=========
* supervisord to start celery, modify ansible playbook to set up supervisord <- Chris
* host relationships in DB, last launch job status per host, etc (self.play.inventory) <- Chris
* stats attributes on launch job (??)
* make launch job rest triggerable & launch job statuses readable.  launch_job.start() <-- MPD
* Chris ---- callback plugin calls external script <-- Chris
  ansible_delegate_callback calls ACOM_DATABASE_LOGGER script ?
* do we need something other than default playbook (ProjectOptions) <-- BOTH, TBD
* way to send cntrl-c to kill job (method on job?) <-- Chris, low priority
* documentation on how to run with callbacks from NOT a launchjob <-- Chris
* interactive SSH agent support for launch jobs/creds
* michael to modify ansible to accept ssh password and sudo password from env vars

REST TODO
---------
* project/teams
* credentials objects
* tags
* audit trails
* launch jobs
* related resources on everything that makes sense
* expose log data from callback (decide on structure)

LATER
-----

* acom logging callback
* UI layer
* CLI client (and libs)
* clean up initial migrations
* init scripts, Apache proxying, etc
* does inventory script need any caching
* credentials subsystem -- let app hold on to keys for user

TWEAKS/ASSORTED
---------------

* project should be able to define an inventory path and if NOT set it in launch job it could come from the project
* add a synthetic bit to the organization to indicate if the current user is an administator of it
* uniqueness checks for playbook paths?
* allow multiple playbook execution types per project, different --tag choices, different --limit choices (maybe just free form in the job for now?)
* permissions infrastructure about who can kick off what kind of jobs
* root API discovery resource at /api and /api/v1
* audit/test read only fields like creation_date

