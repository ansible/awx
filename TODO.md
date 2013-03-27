TODO items for ansible commander
================================

(merge code)

NEXT STEPS

* Michael -- flesh out REST model & tests for everything, API guide
* Chris ---- document celery devs stuff.
* Chris ---- inventory script is done, integrate with celery system, make celery REST triggerable, callback plugin
* Michael -- enhance callback plugin to provide runner and playbook context

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

