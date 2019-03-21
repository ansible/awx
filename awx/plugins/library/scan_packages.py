#!/usr/bin/env python

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
#        "packages": {
#              "libbz2-1.0": [
#                {
#                  "version": "1.0.6-5",
#                  "source": "apt",
#                  "arch": "amd64",
#                  "name": "libbz2-1.0"
#                }
#              ],
#              "patch": [
#                {
#                  "version": "2.7.1-4ubuntu1",
#                  "source": "apt",
#                  "arch": "amd64",
#                  "name": "patch"
#                }
#              ],
#              "gcc-4.8-base": [
#                {
#                  "version": "4.8.2-19ubuntu1",
#                  "source": "apt",
#                  "arch": "amd64",
#                  "name": "gcc-4.8-base"
#                },
#                {
#                  "version": "4.9.2-19ubuntu1",
#                  "source": "apt",
#                  "arch": "amd64",
#                  "name": "gcc-4.8-base"
#                }
#              ]
#       }
'''


def rpm_package_list():
    import rpm
    trans_set = rpm.TransactionSet()
    installed_packages = {}
    for package in trans_set.dbMatch():
        package_details = dict(name=package[rpm.RPMTAG_NAME],
                               version=package[rpm.RPMTAG_VERSION],
                               release=package[rpm.RPMTAG_RELEASE],
                               epoch=package[rpm.RPMTAG_EPOCH],
                               arch=package[rpm.RPMTAG_ARCH],
                               source='rpm')
        if package_details['name'] not in installed_packages:
            installed_packages[package_details['name']] = [package_details]
        else:
            installed_packages[package_details['name']].append(package_details)
    return installed_packages


def deb_package_list():
    import apt
    apt_cache = apt.Cache()
    installed_packages = {}
    apt_installed_packages = [pk for pk in apt_cache.keys() if apt_cache[pk].is_installed]
    for package in apt_installed_packages:
        ac_pkg = apt_cache[package].installed
        package_details = dict(name=package,
                               version=ac_pkg.version,
                               arch=ac_pkg.architecture,
                               source='apt')
        if package_details['name'] not in installed_packages:
            installed_packages[package_details['name']] = [package_details]
        else:
            installed_packages[package_details['name']].append(package_details)
    return installed_packages


def main():
    module = AnsibleModule(  # noqa
        argument_spec = dict(os_family=dict(required=True))
    )
    ans_os = module.params['os_family']
    if ans_os in ('RedHat', 'Suse', 'openSUSE Leap'):
        packages = rpm_package_list()
    elif ans_os == 'Debian':
        packages = deb_package_list()
    else:
        packages = None

    if packages is not None:
        results = dict(ansible_facts=dict(packages=packages))
    else:
        results = dict(skipped=True, msg="Unsupported Distribution")
    module.exit_json(**results)


main()
