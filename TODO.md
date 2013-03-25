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
* CLI client (and libs)
* clean up initial migrations
* init scripts, Apache proxying, etc
* does inventory script need any caching
* credentials subsystem -- let app hold on to keys for user

TWEAKS/ASSORTED
---------------

* add a synthetic bit to the organization to indicate if the current user is an administator of it
* uniqueness checks for playbook paths?
* allow multiple playbook execution types per project, different --tag choices, different --limit choices (maybe just free form in the job for now?)
* permissions infrastructure about who can kick off what kind of jobs
* it would be nice if POSTs to subcollections used the permissions of the regular collection POST rules and then called the PUT code.

