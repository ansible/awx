import os
import glob
import shutil
from setuptools import setup, find_packages, Command


def get_version():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    version_file = os.path.join(current_dir, 'VERSION')
    with open(version_file, 'r') as file:
        return file.read().strip()


class CleanCommand(Command):
    description = "Custom clean command that forcefully removes dist/build directories"
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd

        # List of things to remove
        rm_list = list()

        # Find any .pyc files or __pycache__ dirs
        for root, dirs, files in os.walk(self.cwd, topdown=False):
            for fname in files:
                if fname.endswith('.pyc') and os.path.isfile(os.path.join(root, fname)):
                    rm_list.append(os.path.join(root, fname))
            if root.endswith('__pycache__'):
                rm_list.append(root)

        # Find egg's
        for egg_dir in glob.glob('*.egg') + glob.glob('*egg-info'):
            rm_list.append(egg_dir)

        # Zap!
        for rm in rm_list:
            if self.verbose:
                print("Removing '%s'" % rm)
            if os.path.isdir(rm):
                if not self.dry_run:
                    shutil.rmtree(rm)
            else:
                if not self.dry_run:
                    os.remove(rm)


setup(
    name='awxkit',
    version=get_version(),
    description='The official command line interface for Ansible AWX',
    author='Red Hat, Inc.',
    author_email='info@ansible.com',
    url='https://github.com/ansible/awx',
    packages=find_packages(exclude=['test']),
    cmdclass={
        'clean': CleanCommand,
    },
    include_package_data=True,
    install_requires=[
        'PyYAML',
        'requests',
    ],
    python_requires=">=3.6",
    extras_require={
        'formatting': ['jq'],
        'websockets': ['websocket-client>0.54.0'],
        'crypto': ['cryptography']
    },
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
    ],
    entry_points={
        'console_scripts': [
            'akit=awxkit.scripts.basic_session:load_interactive',
            'awx=awxkit.cli:run'
        ]
    }
)
