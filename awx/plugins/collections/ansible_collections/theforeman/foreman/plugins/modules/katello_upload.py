#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, Eric D Helms <ericdhelms@gmail.com>
# (c) 2018, Sean O'Keeffe <seanokeeffe797@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: katello_upload
short_description: Upload content to Katello
description:
  - Allows the upload of content to a Katello repository
author: "Eric D Helms (@ehelms)"
requirements:
  - python-debian (For deb Package upload)
  - rpm (For rpm upload)
options:
  src:
    description:
      - File to upload
    required: true
    type: path
    aliases:
      - file
  repository:
    description:
      - Repository to upload file in to
    required: true
    type: str
  product:
    description:
      - Product to which the repository lives in
    required: true
    type: str
  organization:
    description:
      - Organization that the Product is in
    required: true
    type: str
notes:
  - Currently only uploading to deb, RPM & file repositories is supported
  - For anything but file repositories, a supporting library must be installed. See Requirements.
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Upload my.rpm"
  katello_upload:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    src: "my.rpm"
    repository: "Build RPMs"
    product: "My Product"
    organization: "Default Organization"
'''

RETURN = ''' # '''

import os
import hashlib
import traceback

from ansible.module_utils.foreman_helper import KatelloAnsibleModule

try:
    from debian import debfile
    HAS_DEBFILE = True
except ImportError:
    HAS_DEBFILE = False
    DEBFILE_IMP_ERR = traceback.format_exc()

try:
    import rpm
    HAS_RPM = True
except ImportError:
    HAS_RPM = False
    RPM_IMP_ERR = traceback.format_exc()

CONTENT_CHUNK_SIZE = 2 * 1024 * 1024


def get_deb_info(path):
    control = debfile.DebFile(path).debcontrol()
    return control['package'], control['version'], control['architecture']


def get_rpm_info(path):
    ts = rpm.TransactionSet()

    # disable signature checks, we might not have the key or the file might be unsigned
    # pre 4.15 RPM needs to use the old name of the bitmask
    try:
        vsflags = rpm.RPMVSF_MASK_NOSIGNATURES
    except AttributeError:
        vsflags = rpm._RPMVSF_NOSIGNATURES
    ts.setVSFlags(vsflags)

    with open(path) as rpmfile:
        rpmhdr = ts.hdrFromFdno(rpmfile)

    name = rpmhdr[rpm.RPMTAG_NAME].decode('ascii')
    epoch = rpmhdr[rpm.RPMTAG_EPOCHNUM]
    version = rpmhdr[rpm.RPMTAG_VERSION].decode('ascii')
    release = rpmhdr[rpm.RPMTAG_RELEASE].decode('ascii')
    arch = rpmhdr[rpm.RPMTAG_ARCH].decode('ascii')

    return (name, epoch, version, release, arch)


def main():
    module = KatelloAnsibleModule(
        argument_spec=dict(
            src=dict(required=True, type='path', aliases=['file']),
            repository=dict(required=True),
            product=dict(required=True),
            organization=dict(required=True),
        ),
    )

    entity_dict = module.clean_params()

    module.connect()

    entity_dict['organization'] = module.find_resource_by_name('organizations', entity_dict['organization'], thin=True)
    scope = {'organization_id': entity_dict['organization']['id']}
    entity_dict['product'] = module.find_resource_by_name('products', entity_dict['product'], params=scope, thin=True)
    product_scope = {'product_id': entity_dict['product']['id']}
    entity_dict['repository'] = module.find_resource_by_name('repositories', entity_dict['repository'], params=product_scope)
    repository_scope = {'repository_id': entity_dict['repository']['id']}

    filename = os.path.basename(entity_dict['src'])

    checksum = hashlib.sha256()
    with open(entity_dict['src'], 'rb') as contentfile:
        for chunk in iter(lambda: contentfile.read(CONTENT_CHUNK_SIZE), b""):
            checksum.update(chunk)
    checksum = checksum.hexdigest()

    content_unit = None
    if entity_dict['repository']['content_type'] == 'deb':
        if not HAS_DEBFILE:
            module.fail_json(msg='The python-debian module is required', exception=DEBFILE_IMP_ERR)

        name, version, architecture = get_deb_info(entity_dict['src'])
        query = 'name = "{0}" and version = "{1}" and architecture = "{2}"'.format(name, version, architecture)
        content_unit = module.find_resource('debs', query, params=repository_scope, failsafe=True)
    elif entity_dict['repository']['content_type'] == 'yum':
        if not HAS_RPM:
            module.fail_json(msg='The rpm Python module is required', exception=RPM_IMP_ERR)

        name, epoch, version, release, arch = get_rpm_info(entity_dict['src'])
        query = 'name = "{0}" and epoch = "{1}" and version = "{2}" and release = "{3}" and arch = "{4}"'.format(name, epoch, version, release, arch)
        content_unit = module.find_resource('packages', query, params=repository_scope, failsafe=True)
    elif entity_dict['repository']['content_type'] == 'file':
        query = 'name = "{0}" and checksum = "{1}"'.format(filename, checksum)
        content_unit = module.find_resource('file_units', query, params=repository_scope, failsafe=True)
    else:
        # possible types in 3.12: docker, ostree, yum, puppet, file, deb
        module.fail_json(msg="Uploading to a {0} repository is not supported yet.".format(entity_dict['repository']['content_type']))

    changed = False
    if not content_unit:
        _content_upload_changed, content_upload = module.resource_action('content_uploads', 'create', repository_scope)
        content_upload_scope = {'id': content_upload['upload_id']}
        content_upload_scope.update(repository_scope)

        offset = 0

        with open(entity_dict['src'], 'rb') as contentfile:
            for chunk in iter(lambda: contentfile.read(CONTENT_CHUNK_SIZE), b""):
                data = {'content': chunk, 'offset': offset}
                module.resource_action('content_uploads', 'update', params=content_upload_scope, data=data)

                offset += len(chunk)

        uploads = [{'id': content_upload['upload_id'], 'name': filename,
                    'size': offset, 'checksum': checksum}]
        import_params = {'id': entity_dict['repository']['id'], 'uploads': uploads}
        module.resource_action('repositories', 'import_uploads', import_params)

        module.resource_action('content_uploads', 'destroy', content_upload_scope)

        changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
