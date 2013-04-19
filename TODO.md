TODO items for ansible commander
================================

CC TODO
=======
* supervisord to start celery, modify ansible playbook to set up supervisord <- ChrisC
* documentation on how to run with callbacks from NOT a launchjob <-- ChrisC
* interactive SSH agent support for launch jobs/creds <-- ChrisC
* michael to modify ansible to accept ssh password and sudo password from env vars
* way to send cntrl-c to kill job (method on job?) <-- ChrisC, low priority 
* default_playbook should be relative to scm_repository and not allow "../" out of the directory

* do we need something other than default playbook (ProjectOptions) <-- MPD later
* make a way to start a job via the API (create a new job) <-- MPD
* make job rest triggerable & job status readable.  now happens just by creating a new job <-- MPD
* figure out how to mark each object generically w/ whether it can be edited/etc
* if you delete a subgroup, hosts go up to parent
* verify unique_together on inventory and host name

* finish REST around permissions <-- MPD

* tags (later)
* audit trails (later)
* related resources on everything that makes sense <--- MPD, important
* make /api and /api/v1 have useful content in it

LATER
=====
* clean up initial migrations
* init scripts (supervisord), Apache proxying, etc
* support multiple project launch options (different flags, etc)


TWEAKS/ASSORTED
---------------

* security check - playbook must be fully pathed when executed by commander and relative to project
directory.  Project directories must be unique and be (also no ../, etc).  default_playbook MUST be a relative path (no starting with . or / or containing ..).
* idea: when creating a project, write a '.acom' file, this file contains a JSON list of valid project GUIDs that are allowed to use it.  This can be created automatically by the system if it does not already exist, but not overwritten by the system.
* document multi-org content limitations with regard to access security and sensitive vars
* when app starts it creates a default organization and all superusers are automatically added to it
* audit/test read only fields like creation_date
* ability to import inventory from script (adds variables and merges, does not override, does not remove anything) -- merge control, possibly via script
* ability to import inventory from inventory files (upgrade case) -- write a inventory script that is ansible-inventory API compatible maybe?
* when associating inventory objects, objects should share common inventory records (user_can_attach method should check)
* permissions on launching a job should be same as creating a job template
* should be able to access permissions as subcollection off of users or teams (no need for permissions tab)

QUESTIONS
---------

* if creating a new project, do we want to have an appliance style path for them, like /storage/projects/GUID ??? may want to keep somewhere else ?

* for dashboard purposes, should there be a URL where I can see all hosts in an inventory whose last job status
  is a failed playbook run?
* what else do we need for dashboarding?



