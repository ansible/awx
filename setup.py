#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import os, datetime, glob, sys
from distutils import log
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist


from awx import __version__

build_timestamp = os.getenv("BUILD",datetime.datetime.now().strftime('-%Y%m%d%H%M'))

# Paths we'll use later
etcpath = "/etc/awx"
homedir = "/var/lib/awx"
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

class sdist_awx(_sdist, object):
    '''
    Custom sdist command to distribute some files as .pyc only.
    '''

    def make_release_tree(self, base_dir, files):
        for f in files[:]:
            if f.endswith('.egg-info/SOURCES.txt'):
                files.remove(f)
                sources_txt_path = f
        super(sdist_awx, self).make_release_tree(base_dir, files)
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
            if f.endswith('.py'):
                log.info('using pyc for: %s', f)
                py_compile.compile(f, doraise=True)
                self.filelist.files[n] = f + 'c'
                self.pyc_only_files.append(f)
        super(sdist_awx, self).make_distribution()

setup(
    name='awx',
    version=__version__.split("-")[0], # FIXME: Should keep full version here?
    author='AnsibleWorks, Inc.',
    author_email='support@ansibleworks.com',
    description='AWX: API, UI and Task Engine for Ansible',
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
        ],
    },
    data_files = proc_data_files([
            ("%s" % homedir,        ["config/wsgi.py",
                                     "awx/static/favicon.ico",
                                    ]),
            ("%s" % webconfig,      ["config/awx.conf","config/awx-plain.conf"]),
        ]
    ),
    options = {
        'egg_info': {
            'tag_build': '-%s' % build_timestamp,
        },
        'aliases': {
            'dev_build': 'clean --all egg_info sdist_awx',
            'release_build': 'clean --all egg_info -b "" sdist_awx',
        },
    },
    cmdclass = {
        'sdist_awx': sdist_awx,
    },
)
