from setuptools_scm import get_version

version = get_version(root='../..', relative_to=__file__)
print(version)
