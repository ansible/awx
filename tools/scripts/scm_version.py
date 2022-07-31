import os
import sys
import subprocess
import traceback

try:
    from setuptools_scm import get_version
except ModuleNotFoundError:
    sys.stderr.write("Unable to import setuptools-scm, attempting to install now...\n")

    os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    subprocess.check_output([sys.executable, '-m', 'ensurepip'])
    subprocess.check_output([sys.executable, '-m', 'pip', 'install', 'setuptools-scm'])

    from setuptools_scm import get_version

version = get_version(root='../..', relative_to=__file__)
print(version)
