#!/usr/bin/env python

# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

import os, datetime, glob, sys, shutil
from distutils import log
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist

from awx import __version__

if os.getenv('OFFICIAL', 'no') == 'yes':
    build_timestamp = ''
else:
    build_timestamp = '-' + os.getenv("BUILD", datetime.datetime.now().strftime('0.git%Y%m%d%H%M'))

# Paths we'll use later
etcpath = "/etc/tower"
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
                                        "tools/munin_monitors/redis_alive",
                                        "tools/munin_monitors/socketio_alive",
                                        "tools/munin_monitors/taskmanager_alive"]),
            ("%s" % munin_plugin_conf_path, ["config/awx_munin_tower_jobs"]),
            ("%s" % sysinit, ["tools/scripts/ansible-tower"]),
            ("%s" % sosconfig, ["tools/sosreport/tower.py"]),
        ]
    ),
    options = {
        'egg_info': {
            'tag_build': build_timestamp,
        },
        'aliases': {
            'dev_build': 'clean --all egg_info sdist',
            'release_build': 'clean --all egg_info -b "" sdist',
        },
    },
)
