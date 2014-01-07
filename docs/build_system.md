AWX Build and Release Process
=============================

This document describes the AWX Software build and release process.
This process includes the automation of the packaging for Debian/Ubuntu
and Fedora/EL (Enterprise Linux), as well as the creation of various
software repositories which are used by the default playbook setup. 

Packaging Details
-----------------------------

### Version and Release Determination ###

The VERSION and RELEASE variables used by the build process are configured
in the Makefile, and are based on the `__version__` field contained within
the `awx/__init__.py file.` This string should always be of the format:

    version-release

There should only be one "-" contained in the string.  (Which can represent
a build/rev type release number).  Example:
 
   1.2.2-0

### OFFICIAL vs. Non-OFFICIAL Builds ###

An "official" build is one that does not include a development timestamp
in the release field. This is controlled by setting the environment variable
`OFFICIAL=yes` prior to running the make command.

Non-official builds will replace the `RELEASE` variable with the following string:

    -devYYYYmmDDHHMM

Non-official builds should only be used for development purposes, and are
copied into the nightly repos. Official builds will be copied out to the 
production servers via the automated Jenkins build process (described below).

### Python sdist Process ###

The sdist build is the first step in the packaging process. This step is 
responsible for assembling the files to be packaged into a .tar.gz, which
can then be installed itself via pip or used later for the RPM/DEB builds.

We are currently overriding the default python sdist function, as we are 
pre-compiling all .py files into .pyc's and removing the plain source. This 
is handled by the function `sdist_awx()` in `setup.py`.

The resulting tar.gz file will be named:

    awx-${VERSION}-${RELEASE}.tar.gz

### RPM Build Process ###

The first step of the RPM build process is to remove the `$RELEASE` from the 
tar.gz, since the spec file does not like to include the release. This is 
handled by the `rpmtar` Makefile target, which first unpacks the file, renames
the contained awx directory to simply be `awx-${VERSION}`, and finally re-
packages the file as `awx-${VERSION}.tar.gz`.

The main Makefile target for the rpm build is (unsurprisingly) `rpm`. This copies
the re-formed sdist .tar.gz file into the rpm-build directory and then calls
the rpmbuild command to create the RPM. 

The spec file for this command is `packaging/rpm/awx.spec`. This file is currently
maintained by hand, so any changelog entries must be added to it manually. All
other aspects of the file (source, version, release, etc.) are picked up via
variables that are set by the Makefile and do not need to be updated during 
packaging.

### DEB Build Process ###

The process to build a .deb is somewhat more involved, and I will not get too
involved in the specifics of how the debian packaging works. The main files used
in this packaging are (all found in `packaging/deb/`):

    - awx.dirs
    - awx.install
    - control
    - rules
    - {pre,post}{inst,rm}

The `awx.dirs` file contains the directories (listed as paths relative to the 
build root) that will be created during the packaging.

The `awx.install` file contains a list of files that will be installed directly
by the build process rather than via the `make install` command or other steps. This
is of the format "source destination" (where the destination is also a path
relative to the build root).

The `control` file is functionally similar to the header of a spec file, and
contains things like the package name, requirements, etc.

The `rules` file is really a Makefile, and contains the rules for the build 
process. These rules are based on the type of build you're executing (binary
vs. source, for instance). Since we are building a binary-only .deb package,
the only target we use is the `binary` target.

The pre/post scripts are analogous to the %pre/%post macros in the RPM spec,
and are executed at the various stages of the installation/removal. For 
Debian/Ubuntu, these scripts do quite a bit more than the corresponding RPM 
stages, since RPM packaging guidelines are generally more strict about 
starting/stopping services, etc. during the RPM installation.

In the main `Makefile`, just as with the RPM target, the target for building 
the .deb's is `deb`. This target begins similarly to the rpm target, in that 
it copies the sdist file into the deb-build directory. It then unpacks that 
file there and calls the `dh_make` helper function. This creates several new
directories that are used by the `dpkg-buildpackage` command, most importantly
the `debian` and `DEBIAN` directories (used for the source and binary builds, 
respectively). The generated `debian` directory is removed and replaced with 
the files that are in `packaging/deb/` and the target package name is inserted 
into a file that will be used as a command-line argument to `dpkg-buildpackage`.
This is required, otherwise the build process will try and figure out the
name automatically (and not always successfully).

Finally, `dpkg-buildpackage` is called to build the .deb.

Jenkins
-----------------------------

### Server Information ###

The AnsibleWorks Jenkins server can be found at http://50.116.42.103:8080/

This is a standard Jenkins installation, with the following additional 
plugins installed:

 - Build Authorization Token Root Plugin: 
   This plugin allows build and related REST build triggers be accessed even 
   when anonymous users cannot see Jenkins.
 - Git Client Plugin:
   The standard git client plugin.
 - Git Parameter Plug-In:
   This plugin adds the ability to choose from git repository revisions or tags
 - GitHub API Plugin:
   This plugin provides GitHub API for other plugins.
 - GitHub Plugin:
   This plugin integrates GitHub to Jenkins.
 - Workspace Cleanup Plugin:
   This plugin ensures that the root of the workspace is cleaned out between
   builds to prevent files from previous builds leaking or breaking future builds.

### Server Installation and Configuration ###

The base Jenkins server was installed via apt:

    $ apt-get install jenkins

Since the server OS for the Jenkins server is Ubuntu Raring (13.04). In order to 
execute RPM builds on this server, mock was installed from source as follows:

    $ apt-get install \
      automake \
      git \
      libpython2.7 \
      libsqlite0 \
      libuser1 \
      make \
      python-decoratortools \
      python-libxml2 \
      python-peak.util.decorators \
      python-pycurl \
      python-rpm \
      python-sqlite \
      python-sqlitecachec \
      python-support \
      python-urlgrabber \
      usermode \
      yum \
      yum-utils 
    
    $ git clone git://git.fedorahosted.org/git/mock.git mock
    $ cd mock
    $ ./autogen.sh
    $ automake
    $ ./configure \
      --bindir=/usr/bin \
      --sbindir=/usr/sbin \
      --sysconfdir=/etc \
      --localstatedir=/var/lib \
      --libdir=/usr/lib \
      --includedir=/usr/include \
      --mandir=/usr/man
    $ make install
    $ ln -s /usr/bin/consolehelper /usr/bin/mock

In order to create apt repositories, the reprepro package was also installed.

    $ apt-get install reprepro

### Configured Jobs ###

There are currently three classes of jobs configured in Jenkins:

    - RPM/DEB builds for Ansible Core
    - RPM/DEB builds for AWX (and tar packaging of the setup playbook/scripts)
    - Automated Scans which kick-off the prior two jobs

The automated scans work by checking for new tags in the git repository for
the given project, and when a new one is found, starting the appropriate jobs.
For RPMs, a job is started for each of the supported distributions while for 
DEBs only one job is started. All of these jobs are started with `OFFICIAL=yes`
so that an official package is produced, which will be copied out to the production
repositories (documented below).

> NOTE: The nightly jobs are currently triggered by a cron job in the exact same
> manner as the above jobs, the only difference being that they set OFFICIAL=no 
> and use HEAD as the target tag for the job, so they are always built off of
> the most recent commit at that time. Likewise, the resultant packages are only
> copied to the relevant nightlies repo (also documented below).

### Manual Builds ###

Manual builds can be triggered via the Jenkins GUI. Simply log in and select the
appropriate job, and then click on the "Build with Parameters" link to the left
(or select it from the drop-down that is available from the main jobs list).

You will be presented with a form to enter parameters. The `TARGET_TAG` and `OFFICIAL`
parameters are the same for both RPM and DEB builds, the function of which is 
described above. For RPM builds, there is an addition parameter named `TARGET_DIST`,
which controls the mock environment for the build.

> WARNING: Take extra care when manually triggering an `OFFICIAL` build at this
> time, as the resultant package will automatically be copied to the production
> server and made available for customers to download. 

> NOTE: As of this writing, using the combination of `TARGET_TAG=HEAD` and `OFFICIAL=yes` 
> is allowed, however this will not be the case in the future. This will either be 
> disallowed by failing the job, or the resultant package will be copied to a third
> repository to be used for user-acceptance testing (UAT).

Repositories
-----------------------------

### Nightlies ###

The nightly repositories are hosted on the AnsibleWorks Jenkins server, and can
be found at the following location:

    http://50.116.42.103/awx_nightlies_RTYUIOPOIUYTYU/

There are two sub-folders: `deb/` and `rpm/`.

The `rpm/` folder itself contains sub-folders for each distribution/architecture
that we support, for example:

    - epel-6-{i386,x86_64}
    - fedora-17-{i386,x86_64}
    - fedora-18-{i386,x86_64}
    - fedora-19-{i386,x86_64}

The `deb/` folder contains several subfolders, which correspond to the normal 
apt repository structure. All .deb files are located under `pool/`, while the `dists/`
directory contains the distribution-specific information.

These nightly repositories can be used by the AWX setup playbook by running the
`setup.sh` shell script with the following option:

    ./setup.sh -e "aw_repo_url=http://50.116.42.103/awx_nightlies_RTYUIOPOIUYTYU"

> Note that if this is not a fresh installation, you should run the following:
> "yum clean all --enablerepo=ansibleworks-awx" in order to clean out the yum cache.

### Official Releases ###

As noted above, `OFFICIAL` builds are copied out to the production server, and can be
found at the following location:

    http://releases.ansible.com/awx/

The AWX setup playbook will use this repo location by default.



