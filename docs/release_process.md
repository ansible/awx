Release Process
===============

This document describes the process of created and publishing an Ansible Tower release.

Time for a release
------------------

When the time comes for a release, the first step is to tag the release in git.

    # git tag <X.Y.Z>

Monitor Jenkins
---------------
Once tagged, [Jenkins](http://50.116.42.103/view/Tower/) will take care of the
following steps.  The jenkins job
[Release_Tower](http://50.116.42.103/view/Tower/job/Release_Tower/) will detect
the recent tag, and initiate the `OFFICIAL=yes` build process.

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
PDF documentation is not currently automated.  The [Build_Tower_Docs](http://50.116.42.103/view/Tower/) job generates HTML documentation, which is not currently published.  Please contact <dave@ansible.com> to request updated PDF documentation.
