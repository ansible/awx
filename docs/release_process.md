Release Process
===============

This document describes the process of creating and publishing an Ansible Tower release.

Time for a release
------------------

When the time comes for a release, the following steps will ensure a smooth and
successful release.

1. Verify that the `__version__` variable has been updated in `awx/__init__.py`.

```
    __version__ = 'X.Y.Z'
```

2. Update the "Release History" in the file `README.md`.

3. Update the rpm package changelog by adding a new entry to the file `packaging/rpm/ansible-tower.spec`.

4. Update the debian package changelog by adding a new entry to the file `packaging/debian/changelog`.

5. Tag and push the release to git.

```
    git tag <X.Y.Z>
    git push --tags
```

6. Create and push a release branch to git.

```
    git branch release_<X.Y.Z>
    git checkout release_<X.Y.Z>
    git push origin release_<X.Y.Z>
```

Monitor Jenkins
---------------
Once tagged, one must launch the [Release_Tower](http://50.116.42.103/view/Tower/job/Release_Tower/) with the following parameters:
* `GIT_BRANCH=origin/tags/<X.Y.Z>`
* `OFFICIAL=yes`

The following jobs will be triggered:
* [Build_Tower_TAR](http://50.116.42.103/view/Tower/)
* [Build_Tower_DEB](http://50.116.42.103/view/Tower/)
  * [Build_Tower_AMI](http://50.116.42.103/view/Tower/)
* [Build_Tower_RPM](http://50.116.42.103/view/Tower/)
* [Build_Tower_Docs](http://50.116.42.103/view/Tower/)

Should any build step fail, Jenkins will emit a message in IRC and set the build status to failed.

Publishing Builds
-----------------
Upon successful completion, jenkins will publish build artifacts to the following locations:

* http://releases.ansible.com/ansible-tower/rpm
* http://releases.ansible.com/ansible-tower/deb
* http://releases.ansible.com/ansible-tower/setup
* http://releases.ansible.com/ansible-tower/docs

Publishing AMI's
----------------------
While OFFICIAL Tower AMI's are created by jenkins, the process for blessing AMI's is manual.  Please contact <dave@ansible.com> to initiate the process.

Publishing Documentation
------------------------
Tower documentation is available in the [product-docs](https://github.com/ansible/product-docs) repository.  The [Build_Tower_Docs](http://50.116.42.103/view/Tower/) job builds and publishes PDF, and HTML, documentation.
