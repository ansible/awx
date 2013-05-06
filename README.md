Ansible-Commander
=================

Ansible-commander is a set of add-ons on top of ansible-core that adds a server,
REST API, cli client, extensive logging, background job execution, and a 
user interface.

Technology
==========

* Ansible
* Django (a python web framework)
* Django REST Framework
* Celery (a python task engine)
* PostgreSQL

Status
======

Ansible-Commander (ACOM) is in very early development and is of interest
to development audiences only.  Open development is important though so
we are building it in the open.

Getting Things Installed
========================

See SETUP.md for requirements and details.

Accessing the new UI
====================

The UI is installed under lib/static/web. After starting the django server
(i.e. make runserver), access the ui from a web browser at:

http://127.0.0.1:8013/static/web/app/index.html

License
=======

Ansible-Commander is made available under the GPL v3, see COPYING, (C) AnsibleWorks, 2013.

Commercial licensing is also available.


