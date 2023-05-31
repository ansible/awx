import os
import sys
import subprocess

try:
    from setuptools_scm import get_version
except ModuleNotFoundError:
    sys.stderr.write("Unable to import setuptools-scm, attempting to install now...\n")

    os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    COMMANDS = ([sys.executable, '-m', 'ensurepip'], [sys.executable, '-m', 'pip', 'install', 'setuptools-scm'])
    for cmd in COMMANDS:
        # capture_output because we only want to print version to stdout if successful
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode:
            # failed, we have no version, so print output so that users can debug
            raise Exception(f'\nCommand `{" ".join(cmd)}` failed (rc={result.returncode}).\n\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}')

    from setuptools_scm import get_version

version = get_version(root='../..', relative_to=__file__)
print(version)
