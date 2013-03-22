TODO items for ansible commander
================================

(merge code)

NEXT STEPS

* Michael -- flesh out REST model & tests for everything, complete tests for PUT to subresources, possible continued permission code cleanup
* Chris ---- document celery devs stuff.  
* Chris ---- inventory script is done, integrate with celery system, make celery REST triggerable, callback plugin
* Michael -- enhance callback plugin to provide runner and playbook context

LATER

* UI layer
* CLI client
* clean up initial migrations
* init scripts, Apache proxying, etc
* does inventory script need any caching
* credentials subsystem -- let app hold on to keys for user

ASSORTED QUESTIONS

* uniqueness checks for playbook paths?
* allow multiple playbook execution types per project, different tag choices (Projects/Runnables?)
* permissions infrastructure about who can kick off what kind of jobs


