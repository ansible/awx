#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import os, datetime, glob, sys
from setuptools import setup, find_packages

from ansibleworks import __version__

build_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')

# Paths we'll use later
etcpath = "/etc/ansibleworks"
homedir = "/var/lib/ansibleworks"
if os.path.exists("/etc/debian_version"):
    webconfig  = "/etc/apache2/conf.d"
else:
    webconfig  = "/etc/httpd/conf.d"

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
    name='ansibleworks',
    version=__version__.split("-")[0], # FIXME: Should keep full version here?
    author='AnsibleWorks, Inc.',
    author_email='support@ansibleworks.com',
    description='AnsibleWorks API, UI and Task Engine',
    long_description='AnsibleWorks API, UI and Task Engine',
    license='Proprietary',
    keywords='ansible',
    url='http://github.com/ansible/ansible-commander',
    packages=['ansibleworks'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Django>=1.5',
        'django-celery',
        'django-extensions',
        'django-filter',
        'django-jsonfield',
        'django-taggit',
        'djangorestframework>=2.3.0,<2.4.0',
        'pexpect',
        'python-dateutil',
        'PyYAML',
        'requests',
        'South>=0.8,<2.0',
    ],
    setup_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
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
            'ansibleworks-manage = ansibleworks:manage',
        ],
    },
    data_files = proc_data_files([
            ("%s" % homedir,        ["ansibleworks/wsgi.py",
                                     "ansibleworks/static/favicon.ico",
                                    ]),
            ("%s" % etcpath,        ["config/settings.py"]),
            ("%s" % webconfig,      ["config/ansibleworks.conf"]),
        ]
    ),
    options={
        'egg_info': {
            'tag_build': '-dev%s' % build_timestamp,
        },
        'aliases': {
            'dev_build': 'clean --all egg_info sdist',
            'release_build': 'clean --all egg_info -b "" sdist',
        },
    },
)

