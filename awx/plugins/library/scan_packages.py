#!/usr/bin/env python

import os
from ansible.module_utils.basic import *

def rpm_package_list():
    import rpm
    trans_set = rpm.TransactionSet()
    installed_packages = []
    for package in trans_set.dbMatch():
        installed_packages.append({'name': package['name'],
                                   'version': "%s" % (package['version'])})
    return installed_packages

def deb_package_list():
    import apt
    apt_cache = apt.Cache()
    installed_packages = []
    apt_installed_packages = [pk for pk in apt_cache.keys() if apt_cache[pk].is_installed]
    for package in apt_installed_packages:
        installed_packages.append({'name': package,
                                   'version': apt_cache[package].installed.version})
    return installed_packages

def main():
    module = AnsibleModule(
        argument_spec = dict())

    packages = []
    if os.path.exists("/etc/redhat-release"):
        packages = rpm_package_list()
    elif os.path.exists("/etc/os-release"):
        packages = deb_package_list()
    results = dict(ansible_facts=dict(packages=packages))
    module.exit_json(**results)

main()
