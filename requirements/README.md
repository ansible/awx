The requirements.txt and requirements_ansible.txt files are generated from requirements.in and requirements_ansible.in, respectively, using `pip-tools` `pip-compile`. The following commands should do this if ran inside the tower_tools container.

NOTE: before running `pip-compile`, please copy-paste contents in `requirements/requirements_git.txt` to the top of `requirements/requirements.in` and prepend each copied line with `-e `. Later after `requirements.txt` is generated, don't forget to remove all `git+https://github.com...`-like lines from both `requirements.txt` and `requirements.in`

```
virtualenv /buildit
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

* Packages `gevent-websocket` and `twisted` are put in `requirements.in` *not* because they are primary dependency of Tower, but because their versions needs to be freezed as dependencies of django channel. Please be mindful when doing dependency updates.

* Package `docutils`, as an upstream of `boto3`, is commented out in both `requirements.txt` and `requirements_ansible.txt` because the official package has a bug that causes RPM build failure. [Here](https://sourceforge.net/p/docutils/bugs/321/) is the bug report. Please do not uncomment it before the bug fix lands. For now we are using [a monkey-patch version of `docutils`](https://github.com/ansible/docutils.git) that comes with the bug fix. It's included in `requirements_git.txt` and `requirements_ansible_git.txt`.
