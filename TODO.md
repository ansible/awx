TODO items for ansible commander
================================

(merge code)

NEXT STEPS

* Michael -- flesh out REST model & tests for everything, API guide
* Chris ---- document celery devs stuff.  
* Chris ---- inventory script is done, integrate with celery system, make celery REST triggerable, callback plugin
* Michael -- enhance callback plugin to provide runner and playbook context

LATER
-----

* UI layer
* CLI client
* clean up initial migrations
* init scripts, Apache proxying, etc
* does inventory script need any caching
* credentials subsystem -- let app hold on to keys for user

TWEAKS
------

* add a synthetic bit to the organization to indicate if the current user is an administator of it
* add related resources to the user object to they can quickly find organizations they are an admin of, organizations, teams, projects, etc

ASSORTED
-------

* uniqueness checks for playbook paths?
* allow multiple playbook execution types per project, different tag choices (Projects/Runnables?)
* permissions infrastructure about who can kick off what kind of jobs


