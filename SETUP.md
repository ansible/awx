SETUP
=====

This will be an ansible playbook soon!

For now these are instructions for CentOS 6.

Install ansible-commander
=========================

Before proceeding, be aware that this should be installed on it's own 
machine (or virtualmachine) as it is going to lock down the database.

Ansible will install ansible-commander using a playbook, so you first
need to have ansible installed.  Do this first and come back here.

You will also need the EPEL yum repository installed if using CentOS6.

First edit app_setup/vars/vars.yml to select a database password.

Edit your local settings in app-setup/templates/local_settings.py.j2
as desired.

run "make setup" to run the ansible setup playbook.  It should run
without erros.

This playbook will:

  * install Django and required software components
  * install postgresql and configure authentication
  * initialize the database
  * initialize the first database table
  * synchronize the database and run any migrations

You may run this setup step again as needed as many times
as you like.

Before you login, you must also run "make adduser" to create
a superuser.  This will allow you to login to the app.  There
is no default user.

Test the server
===============

make runserver

access the server on 127.0.0.1:8000

Running through Apache
======================

TODO.



