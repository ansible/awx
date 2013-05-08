Ansible UI
==========
The user interface to Ansible Commander


Installation
------------
To use the UI you will first need to complete the installation of Ansible Commander. Within 
Ansbile Commander you should be able to start the server (make runserver) and log into the 
admin console. If that all works, then you are ready to install Ansible UI. 

For now the UI runs under the django server installed with Commander. If you are planning to
do development, do NOT pull a copy of UI into the same directory structure as Commander. In 
other words, for development the UI should not be insalled as a subdirectory of Commander.

Once you have obtained a copy of UI, create a symbolic link within the Commander lib/static 
directory that points to the app subdirectory under ansible-ui. Call the link web: 

      cd ~/ansible-commander/lib/static
      ln -s ../../../ansible-ui/app web

With the Ansible Commander server running, you should now be able to access the UI:

      http://127.0.0.1:8013/static/web/index.html

You will be immediately prompted for to log in.  User your Commander superuser credientials.

