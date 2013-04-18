TODO items for ansible commander
================================

4/2 NOTES
=========
* supervisord to start celery, modify ansible playbook to set up supervisord <- ChrisC
* host relationships in DB, last launch job status per host, etc (self.play.inventory) <- ChrisC
* stats attributes on launch job status (??) -- which hosts succeeded, failed, etc (through relationship) <-- Chris C
* make launch job rest triggerable & launch job statuses readable.  launch_job.start() <-- MPD
* do we need something other than default playbook (ProjectOptions) <-- me, later
* way to send cntrl-c to kill job (method on job?) <-- ChrisC, low priority 
* documentation on how to run with callbacks from NOT a launchjob <-- ChrisC
* interactive SSH agent support for launch jobs/creds <-- ChrisC
* michael to modify ansible to accept ssh password and sudo password from env vars

CH notes
========
need to add api/v1/group/N/all_hosts
need to add api/v1/host/N/all_groups or make sure it's in the resource
figure out how to mark each object generically w/ whether it can be edited/etc
enable generic filtering
sorting?
if you delete a subgroup, hosts go up to parent
verify unique_together on inventory and host name

make a way to start a launch job via the API.

future feature of being able to create SavedLaunchJob templates.

REST TODO
---------
* credentials objects & permissions
* tags (later)
* audit trails (later)
* launch jobs triggering <-- important
* related resources on everything that makes sense <--- important
* expose log data from callback (decide on structure)


api/v1/     <-- discoverable
api/v1/me   

{
   id: 2
   foo: 3
   related: [
     'bar' : 'http://api/v1/users/5/bar',
     'baz' : 'http://api/v1/users/10/baz',
   }
}

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
* ability to import inventory from script (adds variables and merges, does not override, does not remove anything)
* ability to import inventory from inventory files (upgrade case)

QUESTIONS
---------

* if creating a project, do we want to have an appliance style path for them, like
  /storage/projects/GUID ??? may want to keep somewhere else ?

MISC
----

when associating inventory objects, objects should share common inventory records (user_can_attach method should check)


PAGINATION, FILTERING, SORTING -> CH


