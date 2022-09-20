ANSIBLE_METADATA = {"metadata_version": "1.0", "status": ["stableinterface"], "supported_by": "community"}


DOCUMENTATION = """
---
module: playbook_integrity
short_description: verify that files within a project have not been tampered with.
description:
  - Makes use of the 'ansible-sign' project as a library for ensuring that an
    Ansible project has not been tampered with.
  - There are multiple types of validation that this action plugin supports,
    currently: GPG public/private key signing of a checksum manifest file, and
    checking the checksum manifest file itself against the checksum of each file
    that is being verified.
  - In the future, other types of validation may be supported.
options:
  project_path:
    description:
      - Directory of the project being verified. Expected to contain a
        C(.ansible-sign) directory with a generated checksum manifest file and a
        detached signature for it. These files are produced by the
        C(ansible-sign) command-line utility.
    required: true
  validation_type:
    description:
      - Describes the kind of validation to perform on the project.
      - I(validation_type=gpg) means that a GPG Public Key credential is being
        used to verify the integrity of the checksum manifest (and therefore the
        project).
      - 'checksum_manifest' means that the signed checksum manifest is validated
        against all files in the project listed by its MANIFEST.in file. Just
        running this plugin with I(validation_type=checksum_manifest) is
        typically B(NOT) enough. It should also be run with a I(validation_type)
        that ensures that the manifest file itself has not changed, such as
        I(validation_type=gpg).
    required: true
    choices:
      - gpg
      - checksum_manifest
  gpg_pubkey:
    description:
      - The public key to validate a checksum manifest against. Must match the
        detached signature in the project's C(.ansible-sign) directory.
      - Required when I(validation_type=gpg).
author:
    - Ansible AWX Team
"""

EXAMPLES = """
    - name: Verify project content using GPG signature
      playbook_integrity:
        project_path: /srv/projects/example
        validation_type: gpg
        gpg_pubkey: |
          -----BEING PGP PUBLIC KEY BLOCK-----

          mWINAFXMtjsACADIf/zJS0V3UO3c+KAUcpVAcChpliM31ICDWydfIfF3dzMzLcCd
          Cj2kk1mPWtP/JHfk1V5czcWWWWGC2Tw4g4IS+LokAAuwk7VKTlI34eeMl8SiZCAI
          [...]

    - name: Verify project content against checksum manifest
      playbook_integrity:
        project_path: /srv/projects/example
        validation_type: checksum_manifest
"""
