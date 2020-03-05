#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Google
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gcp_storage_object
description:
- Upload or download a file from a GCS bucket.
short_description: Creates a GCP Object
version_added: '2.8'
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
- google-cloud-storage >= 1.2..0
options:
  action:
    description:
    - The actions to be taken on this object.
    - You can download the object, upload the object, or delete it.
    required: false
    type: str
    choices:
    - download
    - upload
    - delete
  src:
    description:
    - Source location of file (may be local machine or cloud depending on action).
    required: false
    type: path
  dest:
    description:
    - Destination location of file (may be local machine or cloud depending on action).
    required: false
    type: path
  bucket:
    description:
    - The name of the bucket.
    required: false
    type: str
  project:
    description:
    - The Google Cloud Platform project to use.
    type: str
  auth_kind:
    description:
    - The type of credential used.
    type: str
    required: true
    choices:
    - application
    - machineaccount
    - serviceaccount
  service_account_contents:
    description:
    - The contents of a Service Account JSON file, either in a dictionary or as a
      JSON string that represents it.
    type: jsonarg
  service_account_file:
    description:
    - The path of a Service Account JSON file if serviceaccount is selected as type.
    type: path
  service_account_email:
    description:
    - An optional service account email address if machineaccount is selected and
      the user does not wish to use the default email.
    type: str
  scopes:
    description:
    - Array of scopes to be used
    type: list
  env_type:
    description:
    - Specifies which Ansible environment you're running this module within.
    - This should not be set unless you know what you're doing.
    - This only alters the User Agent string for any API requests.
    type: str
"""

EXAMPLES = """
- name: create a object
  google.cloud.gcp_storage_object:
    action: download
    bucket: ansible-bucket
    src: modules.zip
    dest: "~/modules.zip"
    project: test_project
    auth_kind: serviceaccount
    service_account_file: "/tmp/auth.pem"
    state: present
"""

RETURN = """
bucket:
  description:
  - The bucket where the object is contained.
  returned: download, upload
  type: str
cache_control:
  description:
  - HTTP 'Cache-Control' header for this object
  returned: download, upload
  type: str
chunk_size:
  description:
  - Get the blob's default chunk size
  returned: download, upload
  type: str
media_link:
  description:
  - The link for the media
  returned: download, upload
  type: str
self_link:
  description:
  - The self_link for the media.
  returned: download, upload
  type: str
storage_class:
  description:
  - The storage class for the object.
  returned: download, upload
  type: str
"""

################################################################################
# Imports
################################################################################

from ansible.module_utils.gcp_utils import (
    navigate_hash,
    GcpSession,
    GcpModule,
    GcpRequest,
    replace_resource_dict,
)
import json
import os
import mimetypes
import hashlib
import base64

try:
    import google.cloud
    from google.cloud import storage
    from google.api_core.client_info import ClientInfo
    from google.cloud.storage import Blob

    HAS_GOOGLE_STORAGE_LIBRARY = True
except ImportError:
    HAS_GOOGLE_STORAGE_LIBRARY = False
################################################################################
# Main
################################################################################


def main():
    """Main function"""

    module = GcpModule(
        argument_spec=dict(
            action=dict(type="str", choices=["download", "upload", "delete"]),
            src=dict(type="path"),
            dest=dict(type="path"),
            bucket=dict(type="str"),
        )
    )

    if not HAS_GOOGLE_STORAGE_LIBRARY:
        module.fail_json(msg="Please install the google-cloud-storage Python library")

    if not module.params["scopes"]:
        module.params["scopes"] = [
            "https://www.googleapis.com/auth/devstorage.full_control"
        ]

    creds = GcpSession(module, "storage")._credentials()
    client = storage.Client(
        project=module.params['project'],
        credentials=creds, client_info=ClientInfo(user_agent="Google-Ansible-MM-object")
    )

    bucket = client.get_bucket(module.params['bucket'])

    remote_file_exists = Blob(remote_file_path(module), bucket).exists()
    local_file_exists = os.path.isfile(local_file_path(module))

    # Check if files exist.
    results = {}
    if module.params["action"] == "delete" and not remote_file_exists:
        module.fail_json(msg="File does not exist in bucket")

    if module.params["action"] == "download" and not remote_file_exists:
        module.fail_json(msg="File does not exist in bucket")

    if module.params["action"] == "upload" and not local_file_exists:
        module.fail_json(msg="File does not exist on disk")

    if module.params["action"] == "delete":
        if remote_file_exists:
            results = delete_file(module, client, module.params["src"])
            results["changed"] = True
            module.params["changed"] = True

    elif module.params["action"] == "download":
        results = download_file(
            module, client, module.params["src"], module.params["dest"]
        )
        results["changed"] = True

    # Upload
    else:
        results = upload_file(
            module, client, module.params["src"], module.params["dest"]
        )
        results["changed"] = True

    module.exit_json(**results)


def download_file(module, client, name, dest):
    try:
        bucket = client.get_bucket(module.params['bucket'])
        blob = Blob(name, bucket)
        with open(dest, "wb") as file_obj:
            blob.download_to_file(file_obj)
        return blob_to_dict(blob)
    except google.cloud.exceptions.NotFound as e:
        module.fail_json(msg=str(e))


def upload_file(module, client, src, dest):
    try:
        bucket = client.get_bucket(module.params['bucket'])
        blob = Blob(dest, bucket)
        with open(src, "r") as file_obj:
            blob.upload_from_file(file_obj)
        return blob_to_dict(blob)
    except google.cloud.exceptions.GoogleCloudError as e:
        module.fail_json(msg=str(e))


def delete_file(module, client, name):
    try:
        bucket = client.get_bucket(module.params['bucket'])
        blob = Blob(name, bucket)
        blob.delete()
        return {}
    except google.cloud.exceptions.NotFound as e:
        module.fail_json(msg=str(e))


def local_file_path(module):
    if module.params["action"] == "download":
        return module.params["dest"]
    else:
        return module.params["src"]


def remote_file_path(module):
    if module.params["action"] == "download":
        return module.params["src"]
    elif module.params["action"] == "delete":
        return module.params["src"]
    else:
        return module.params["dest"]


def blob_to_dict(blob):
    return {
        'bucket': {
            'name': blob.bucket.path
        },
        'cache_control': blob.cache_control,
        'chunk_size': blob.chunk_size,
        'media_link': blob.media_link,
        'self_link': blob.self_link,
        'storage_class': blob.storage_class
    }


if __name__ == "__main__":
    main()
