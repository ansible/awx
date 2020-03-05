# How to debug modules

Set up debugging using ansible's test-module

```sh
make debug-setup
```

Debug with ansible's test-module

```sh
make debug MODULE=<module name>

# Example: debug the katello_content_view module
$ make debug MODULE=katello_content_view
./.tmp/ansible/hacking/test-module -m modules/katello_content_view.py -a @tests/data/content-view.json -D /usr/lib64/python2.7/pdb.py
...
```

You can set a number of environment variables besides `MODULE` to configure make. Check the [Makefile](https://github.com/theforeman/foreman-ansible-modules/blob/master/Makefile) for more configuration options.
