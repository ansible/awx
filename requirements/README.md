The `requirements.txt` and `requirements_ansible.txt` files are generated from `requirements.in` and `requirements_ansible.in`, respectively, using `pip-tools` `pip-compile`.

Run `./updater.sh` command from inside `./requirements` directory of the awx repository.

Make sure you have `patch, awk, python3, python2, python3-venv, python2-virtualenv, pip2, pip3` installed.

This script will:

  - Update `requirements.txt` based on `requirements.in`
  - Update/generate `requirements_ansible.txt` based on `requirements_ansible.in`
    - including an automated patch that adds `python_version < "3"` for Python 2 backward compatibility
  - Removes the `docutils` dependency line from `requirements.txt` and `requirements_ansible.txt`

You can also upgrade (`pip-compile --upgrade`) the dependencies by running `./updater.sh upgrade`.

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
