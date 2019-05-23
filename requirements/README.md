The requirements.txt and requirements_ansible.txt files are generated from requirements.in and requirements_ansible.in, respectively, using `pip-tools` `pip-compile`. The following commands should do this if ran inside the tools_awx container.

Run these commands from the root of the awx repo. This will produce python 3 requirements files.

```
python3 -m venv /buildit
source /buildit/bin/activate
pip install pip-tools
pip install pip --upgrade

pip-compile -U -r --allow-unsafe --output-file requirements/requirements.txt requirements/requirements.in
pip-compile -U -r --allow-unsafe --output-file requirements/requirements_ansible_py3.txt requirements/requirements_ansible.in
```

Remove the `docutils` line from `requirements/requirements.txt`.

The Ansible venv requirements file needs to start with the python 2 version
as a base. Then we can run the tool again to get the python 3 version.
Consult the output of the `diff` command and add a conditional switch in those cases.

```
virtualenv -p python2 /buildit_py2
source /buildit_py2/bin/activate
pip install pip-tools
pip install pip --upgrade

pip-compile -U -r --allow-unsafe --output-file requirements/requirements_ansible.txt requirements/requirements_ansible.in
diff requirements/requirements_ansible_py3.txt requirements/requirements_ansible.txt
rm requirements/requirements_ansible_py3.txt
```

Python 3 exceptions should be added to relevant `requirements_ansible.txt` lines
after version numbers with the syntax of `; python_version < '3'`.

## Licenses and Source Files

If any library has a change to its license with the upgrade, then the license for that library
inside of `docs/licenses` needs to be updated.

For libraries that have source distribution requirements (LGPL as an example),
a tarball of the library is kept along with the license.
To download the PyPI tarball, you can run this command:

```
pip download <pypi library name> -d docs/licenses/ --no-binary :all: --no-deps
```

Make sure to delete the old tarball if it is an upgrade.
