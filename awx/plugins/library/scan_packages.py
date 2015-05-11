#!/usr/bin/env python

import os
from ansible.module_utils.basic import * # noqa

DOCUMENTATION = '''
---
module: scan_packages
short_description: Return installed packages information as fact data
description:
    - Return information about installed packages as fact data
version_added: "1.9"
options:
requirements: [ ]
author: Matthew Jones
'''

EXAMPLES = '''
# Example fact output:
# host | success >> {
#    "ansible_facts": {
#        "services": [
#            {
#                "source": "apt",
#               "version": "1.0.6-5",
#               "architecture": "amd64",
#               "name": "libbz2-1.0"
#           },
#           {
#               "source": "apt",
#               "version": "2.7.1-4ubuntu1",
#               "architecture": "amd64",
#               "name": "patch"
#           },
#           {
#               "source": "apt",
#               "version": "4.8.2-19ubuntu1",
#               "architecture": "amd64",
#               "name": "gcc-4.8-base"
#           }, ... ] } }
'''

def rpm_package_list():
    import rpm
    trans_set = rpm.TransactionSet()
    installed_packages = []
    for package in trans_set.dbMatch():
        package_details = dict(name=package[rpm.RPMTAG_NAME],
                               version=package[rpm.RPMTAG_VERSION],
                               release=package[rpm.RPMTAG_RELEASE],
                               epoch=package[rpm.RPMTAG_EPOCH],
                               arch=package[rpm.RPMTAG_ARCH],
                               source='rpm')
        installed_packages.append(package_details)
    return installed_packages

def deb_package_list():
    import apt
    apt_cache = apt.Cache()
    installed_packages = []
    apt_installed_packages = [pk for pk in apt_cache.keys() if apt_cache[pk].is_installed]
    for package in apt_installed_packages:
        ac_pkg = apt_cache[package].installed
        package_details = dict(name=package,
                               version=ac_pkg.version,
                               architecture=ac_pkg.architecture,
                               source='apt')
        installed_packages.append(package_details)
    return installed_packages

def main():
    module = AnsibleModule(
        argument_spec = dict())

    packages = []
    # TODO: module_utils/basic.py in ansible contains get_distribution() and get_distribution_version()
    # which can be used here and is accessible by this script instead of this basic detector.
    if os.path.exists("/etc/redhat-release"):
        packages = rpm_package_list()
    elif os.path.exists("/etc/os-release"):
        packages = deb_package_list()
    results = dict(ansible_facts=dict(packages=packages))
    module.exit_json(**results)

main()
