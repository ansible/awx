#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import datetime
from setuptools import setup, find_packages

from ansibleworks import __version__

build_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')

setup(
    name='ansibleworks',
    version=__version__,
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
