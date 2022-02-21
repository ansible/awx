ANSIBLE_METADATA = {"metadata_version": "1.0", "status": ["stableinterface"], "supported_by": "community"}

DOCUMENTATION = """
---
module: playbook_integrity
short_description: verification module for Ansible playbook
version_added: "x.x.x"
description: A module to verify ansible playbook in SCM repo.
options:
  target:
    description:
    - A target name of verification. Directory path for playbook verification.
    required: true
    type: str
  type:
    description:
    - A type of the resource to be verified. ["playbook"]
    - default: "playbook"
    required: false
    type: str
  signature_type:
    description:
    - Signature type which will be used for verification. ["gpg"/"sigstore"/"sigstore_keyless"]
    - default: "gpg"
    required: false
    type: str
  public_key:
    description:
    - A path to your public key for verification. Only when "signature_type" is "gpg" or "sigstore"
    required: false
    type: str
  keyless_signer_id:
    description:
    - A signer id of keyless verification. If specified, the signer id of the provided signature must match with this. Only when "signature_type" is "sigstore_keyless"
    required: false
    type: str
    
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - playbook.integrity.my_doc_fragment_name

author:
    - Hirokuni Kitahara (@hirokuni-kitahara)
"""

EXAMPLES = """
# Verify a playbook SCM repo
- name: Verify a playbook SCM repo
  playbook_integrity:
    target: path/to/playbookrepo
"""
