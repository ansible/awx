#!/usr/bin/env python

# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

import os, datetime, glob, sys, shutil
from distutils import log
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist

from awx import __version__

build_timestamp = os.getenv("BUILD",datetime.datetime.now().strftime('-%Y%m%d%H%M'))

# Paths we'll use later
etcpath = "/etc/awx"
homedir = "/var/lib/awx"
sharedir = "/usr/share/awx"
munin_plugin_path = "/etc/munin/plugins/"
munin_plugin_conf_path = "/etc/munin/plugin-conf.d"

if os.path.exists("/etc/debian_version"):
    sysinit = "/etc/init.d"
    webconfig  = "/etc/apache2/conf.d"
    shutil.copy("config/awx-munin-ubuntu.conf", "config/awx-munin.conf")
    # sosreport-3.1 (and newer) look in '/usr/share/sosreport/sos/plugins'
    # sosreport-3.0 looks in '/usr/lib/python2.7/dist-packages/sos/plugins'
    # debian/<package>.links will create symlinks to support both versions
    sosconfig = "/usr/share/sosreport/sos/plugins"
else:
    sysinit = "/etc/rc.d/init.d"
    webconfig  = "/etc/httpd/conf.d"
    shutil.copy("config/awx-munin-el.conf", "config/awx-munin.conf")
    # The .spec will create symlinks to support multiple versions of sosreport
    sosconfig = "/usr/share/sosreport/sos/plugins"

#####################################################################
# Helper Functions

def explode_glob_path(path):
    """Take a glob and hand back the full recursive expansion,
    ignoring links.
    """

    result = []
    includes = glob.glob(path)
    for item in includes:
        if os.path.isdir(item) and not os.path.islink(item):
            result.extend(explode_glob_path(os.path.join(item, "*")))
        else:
            result.append(item)
    return result


def proc_data_files(data_files):
    """Because data_files doesn't natively support globs...
    let's add them.
    """

    result = []

    # If running in a virtualenv, don't return data files that would install to
    # system paths (mainly useful for running tests via tox).
    if hasattr(sys, 'real_prefix'):
        return result

    for dir,files in data_files:
        includes = []
        for item in files:
            includes.extend(explode_glob_path(item))
        result.append((dir, includes))
    return result

#####################################################################

class sdist_deb(_sdist, object):
    '''
    Custom sdist command to distribute some files as .pyc only.
    '''

    def make_release_tree(self, base_dir, files):
        for f in files[:]:
            if f.endswith('.egg-info/SOURCES.txt'):
                files.remove(f)
                sources_txt_path = f
        super(sdist_deb, self).make_release_tree(base_dir, files)
        new_sources_path = os.path.join(base_dir, sources_txt_path)
        if os.path.isfile(new_sources_path):
            log.warn('unlinking previous %s', new_sources_path)
            os.unlink(new_sources_path)
        log.info('writing new %s', new_sources_path)
        new_sources = file(new_sources_path, 'w')
        for line in file(sources_txt_path, 'r'):
            line = line.strip()
            if line in self.pyc_only_files:
                line = line + 'c'
            new_sources.write(line + '\n')

    def make_distribution(self):
        self.pyc_only_files = []
        import py_compile
        for n, f in enumerate(self.filelist.files[:]):
            if not f.startswith('awx/'):
                continue
            if f.startswith('awx/lib/site-packages'):
                continue
            if f.startswith('awx/scripts'):
                continue
            if f.startswith('awx/plugins'):
                continue
            if f.startswith('awx/main/tests/data'):
                continue
            if f.endswith('.py'):
                log.info('using pyc for: %s', f)
                # Byte compile to create .pyc file
                py_compile.compile(f, doraise=True)
                # Replace .py with .pyc file
                self.filelist.files[n] = f + 'c'
                self.pyc_only_files.append(f)
        super(sdist_deb, self).make_distribution()

#####################################################################

from distutils.command.install_lib import install_lib as _install_lib

class install_lib(_install_lib, object):
    '''
    Custom install_lib command to distribute some files as .pyc only.
    '''

    def run(self):
        '''
        Overload the run method and remove all .py files after compilation
        '''

        super(install_lib, self).run()
        for f in self.install():
            if not f.startswith(self.install_dir + 'awx/'):
                log.debug('install_lib skipping: %s', f)
                continue
            if f.startswith(self.install_dir + 'awx/lib/site-packages'):
                log.debug('install_lib skipping: %s', f)
                continue
            if f.startswith(self.install_dir + 'awx/scripts'):
                log.debug('install_lib skipping: %s', f)
                continue
            if f.startswith(self.install_dir + 'awx/plugins'):
                log.debug('install_lib skipping: %s', f)
                continue
            if f.startswith(self.install_dir + 'awx/main/tests/data'):
                log.debug('install_lib skipping: %s', f)
                continue
            if f.endswith('.py'):
                log.debug('install_lib removing: %s', f)
                os.unlink(f)

    def get_outputs(self):
        '''
        Overload the get_outputs method and remove any .py entries in the file
        list
        '''

        filenames = super(install_lib, self).get_outputs()
        return [filename for filename in filenames
            if not filename.endswith('.py')]

#####################################################################

setup(
    name='ansible-tower',
    version=__version__.split("-")[0], # FIXME: Should keep full version here?
    author='Ansible, Inc.',
    author_email='support@ansible.com',
    description='ansible-tower: API, UI and Task Engine for Ansible',
    long_description='AWX provides a web-based user interface, REST API and '
                     'task engine built on top of Ansible',
    license='Proprietary',
    keywords='ansible',
    url='http://github.com/ansible/ansible-commander',
    packages=['awx'],
    include_package_data=True,
    zip_safe=False,
    setup_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators'
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
    ],
    entry_points = {
        'console_scripts': [
            'awx-manage = awx:manage',
            'tower-manage = awx:manage',
        ],
    },
    data_files = proc_data_files([
            ("%s" % homedir,        ["config/wsgi.py",
                                     "awx/static/favicon.ico",
                                    ]),
            ("%s" % webconfig,      ["config/awx-httpd-80.conf",
                                     "config/awx-httpd-443.conf",
                                     "config/awx-munin.conf",
                                    ]),
            ("%s" % sharedir,       ["tools/scripts/request_tower_configuration.sh",]),
            ("%s" % munin_plugin_path, ["tools/munin_monitors/tower_jobs",
                                        "tools/munin_monitors/callbackr_alive",
                                        "tools/munin_monitors/celery_alive",
                                        "tools/munin_monitors/postgres_alive",
                                        "tools/munin_monitors/rabbit_alive",
                                        "tools/munin_monitors/socketio_alive",
                                        "tools/munin_monitors/taskmanager_alive"]),
            ("%s" % munin_plugin_conf_path, ["config/awx_munin_tower_jobs"]),
            ("%s" % sysinit, ["tools/scripts/ansible-tower"]),
            ("%s" % sosconfig, ["tools/sosreport/tower.py"]),
        ]
    ),
    options = {
        'egg_info': {
            'tag_build': '-%s' % build_timestamp,
        },
        'aliases': {
            # For RPM builds, don't byte-compile awx ... RPM handles that for us
            'dev_rpm': 'clean --all egg_info sdist',
            'release_rpm': 'clean --all egg_info -b "" sdist',
            # For DEB builds, do byte-compile awx
            'dev_deb': 'clean --all egg_info sdist_deb',
            'release_deb': 'clean --all egg_info -b "" sdist_deb',
        },
    },
    cmdclass = {
        'sdist_deb': sdist_deb,
        'install_lib': install_lib,
    },
)
