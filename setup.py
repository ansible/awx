#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup, find_packages

from lib import __version__

setup(
    name='ansible-commander',
    version=__version__,
    author='AnsibleWorks, Inc.',
    author_email='support@ansibleworks.com',
    description='Ansible REST API and background job execution.',
    long_description=file('README.md', 'rb').read(),
    license='Proprietary',
    keywords='ansible',
    url='http://github.com/ansible/ansible-commander',
    packages=['lib'],  # FIXME: Rename to acom?
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Django>=1.5',
        'django-celery',
        'django-devserver',
        'django-extensions',
        'django-filter',
        'django-jsonfield',
        'djangorestframework',
        'pexpect',
        'python-dateutil',
        'PyYAML',
        'South',
    ],
    setup_requires=[],
    #tests_require=[
    #    'Django>=1.5',
    #    'django-celery',
    #    'django-devserver',
    #    'django-extensions',
    #    'django-filter',
    #    'django-jsonfield',
    #    'django-setuptest',
    #    'djangorestframework',
    #    'pexpect',
    #    'python-dateutil',
    #    'PyYAML',
    #    'South',
    #],
    #test_suite='test_suite.TestSuite',
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
            'acom-manage = lib:manage',
        ],
    },
    options={
        'egg_info': {
            'tag_build': '-dev',
        },
        'aliases': {
            'dev_build': 'clean --all egg_info sdist',
            'release_build': 'clean --all egg_info -b "" sdist',
        },
    },
)
