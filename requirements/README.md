The requirements.txt and requirements_ansible.txt files are generated from requirements.in and requirements_ansible.in, respectively, using `pip-tools` `pip-compile`. The following commands should do this if ran inside the tower_tools container.

NOTE: before running `pip-compile`, please copy-paste contents in `requirements/requirements_git.txt` to the top of `requirements/requirements.in` and prepend each copied line with `-e `. Later after `requirements.txt` is generated, don't forget to remove all `git+https://github.com...`-like lines from both `requirements.txt` and `requirements.in` (repeat for `requirements_ansible_git.txt` and `requirements_ansible.in`)

At the end of `requirements/requirements.in`, pip and setuptools need to have their versions pinned.

```
python3 -m venvpip install pip-tools /buildit
source /buildit/bin/activate
pip install pip-tools
pip install pip --upgrade

pip-compile requirements/requirements.in > requirements/requirements.txt
pip-compile requirements/requirements_ansible.in > requirements/requirements_ansible.txt
```

## Known Issues

* Remove the `-e` from packages of the form `-e git+https://github.com...` in the generated `.txt`. Failure to do so will result in a "bad" RPM and DEB due to the `pip install` laying down a symbolic link with an absolute path from the virtualenv to the git repository that will differ from when the RPM and DEB are build to when the RPM and DEB are installed on a machine. By removing the `-e` the symbolic egg link will not be created and all is well.

* As of `pip-tools` `1.8.1` `pip-compile` does not resolve packages specified using a git url. Thus, dependencies for things like `dm.xmlsec.binding` do not get resolved and output to `requirements.txt`. This means that:
  * can't use `pip install --no-deps` because other deps WILL be sucked in
  * all dependencies are NOT captured in our `.txt` files. This means you can't rely on the `.txt` when gathering licenses.
