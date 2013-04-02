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
* credentials objects & permissions
* tags
* audit trails
* launch jobs triggering
* related resources on everything that makes sense
* expose log data from callback (decide on structure)

LATER
-----

* UI layer, CLI client (and libs)
* clean up initial migrations
* init scripts (supervisord), Apache proxying, etc
* does inventory script need any caching (??)
* support multiple project launch options (different flags, etc)


TWEAKS/ASSORTED
---------------

* security check - playbook must be fully pathed when executed by commander and relative to project
directory.  Project directories must be unique and be (also no ../, etc).  default_playbook MUST be a relative path (no starting with . or / or containing ..).
* when creating a project, write a '.acom' file, this file contains a JSON list of valid project GUIDs that are allowed to use it.  This can be created automatically by the system if it does not already exist, but not overwritten by the system.
* document multi-org content limitations with regard to access security and sensitive vars
* when app starts it creates a default organization and all superusers are automatically added to it
* API discovery resource at /api and /api/v1
* audit/test read only fields like creation_date

QUESTIONS
---------

* if creating a project, do we want to have an appliance style path for them, like
  /storage/projects/GUID ??? may want to keep somewhere else ?

