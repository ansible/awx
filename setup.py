#!/usr/bin/env python

# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import os
import glob
import sys
from setuptools import setup
from setuptools.command.egg_info import egg_info as _egg_info


# Paths we'll use later
etcpath = "/etc/tower"
homedir = "/var/lib/awx"
bindir = "/usr/bin"
sharedir = "/usr/share/awx"
docdir = "/usr/share/doc/awx"


def get_version():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    version_file = os.path.join(current_dir, 'VERSION')
    with open(version_file, 'r') as file:
        return file.read().strip()


if os.path.exists("/etc/debian_version"):
    sysinit = "/etc/init.d"
    webconfig  = "/etc/nginx"
    siteconfig = "/etc/nginx/sites-enabled"
    # sosreport-3.1 (and newer) look in '/usr/share/sosreport/sos/plugins'
    # sosreport-3.0 looks in '/usr/lib/python2.7/dist-packages/sos/plugins'
    # debian/<package>.links will create symlinks to support both versions
    sosconfig = "/usr/share/sosreport/sos/plugins"
else:
    sysinit = "/etc/rc.d/init.d"
    webconfig  = "/etc/nginx"
    siteconfig = "/etc/nginx/sites-enabled"
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


class egg_info_dev(_egg_info):
    def find_sources(self):
        # when we generate a .egg-info for the development
        # environment, it's not really critical that we
        # parse the MANIFEST.in (which is actually quite expensive
        # in Docker for Mac)
        pass


#####################################################################


setup(
    name=os.getenv('NAME', 'awx'),
    version=get_version(),
    author='Ansible, Inc.',
    author_email='info@ansible.com',
    description='awx: API, UI and Task Engine for Ansible',
    long_description='AWX provides a web-based user interface, REST API and '
                     'task engine built on top of Ansible',
    license='Apache License 2.0',
    keywords='ansible',
    url='http://github.com/ansible/awx',
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
        'License :: Apache License 2.0',
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
        ],
        'awx.credential_plugins': [
            'conjur = awx.main.credential_plugins.conjur:conjur_plugin',
            'hashivault_kv = awx.main.credential_plugins.hashivault:hashivault_kv_plugin',
            'hashivault_ssh = awx.main.credential_plugins.hashivault:hashivault_ssh_plugin',
            'azure_kv = awx.main.credential_plugins.azure_kv:azure_keyvault_plugin',
            'aim = awx.main.credential_plugins.aim:aim_plugin'
        ]
    },
    data_files = proc_data_files([
        ("%s" % homedir,        ["config/wsgi.py",
                                 "awx/static/favicon.ico"]),
        ("%s" % siteconfig,      ["config/awx-nginx.conf"]),
        #        ("%s" % webconfig,      ["config/uwsgi_params"]),
        ("%s" % sharedir,       ["tools/scripts/request_tower_configuration.sh","tools/scripts/request_tower_configuration.ps1"]),
        ("%s" % docdir,         ["docs/licenses/*",]),
        ("%s" % bindir, ["tools/scripts/ansible-tower-service",
                         "tools/scripts/failure-event-handler",
                         "tools/scripts/awx-python",
                         "tools/scripts/ansible-tower-setup"]),
        ("%s" % sosconfig, ["tools/sosreport/tower.py"])]),
    options = {
        'aliases': {
            'dev_build': 'clean --all egg_info sdist',
            'release_build': 'clean --all egg_info -b "" sdist'
        },
        'build_scripts': {
            'executable': '/usr/bin/awx-python',
        },
    },
    cmdclass={'egg_info_dev': egg_info_dev}
)
