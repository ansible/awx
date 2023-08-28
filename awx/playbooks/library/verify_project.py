ANSIBLE_METADATA = {"metadata_version": "1.0", "status": ["stableinterface"], "supported_by": "community"}


DOCUMENTATION = """
---
module: playbook_integrity
short_description: verify that files within a project have not been tampered with.
description:
  - Makes use of the 'ansible-sign' project as a library for ensuring that an
    Ansible project has not been tampered with.
  - There are multiple types of validation that this action plugin supports,
    currently: GPG public/private key signing and Sigstore signing of a checksum manifest file,
    and checking the checksum manifest file itself against the checksum of each file
    that is being verified.
  - In the future, other types of validation may be supported.
options:
  project_path:
    description:
      - Directory of the project being verified. Expected to contain a
        C(.ansible-sign) directory with a generated checksum manifest file and a
        detached signature (GPG) or Sigstore bundle file (https://github.com/sigstore/sigstore-python#usage)
        for it. These files are produced by the C(ansible-sign) command-line utility.
    required: true
  validation_type:
    description:
      - Describes the kind of validation to perform on the project.
      - I(validation_type=gpg) means that a GPG Public Key credential is being
        used to verify the integrity of the checksum manifest (and therefore the
        project).
      - I(validation_type=sigstore) means that Sigstore verification parameters
        (signer identity, OIDC issuer URL...) are used to to verify the integrity
        of the checksum manifest (and therefore the project).
        Sigstore looks into the project's C(.ansible-sign) directory for a Sigstore
        bundle file (C(.sigstore) file) matching the checksum manifest file.
      - 'checksum_manifest' means that the signed checksum manifest is validated
        against all files in the project listed by its MANIFEST.in file. Just
        running this plugin with I(validation_type=checksum_manifest) is
        typically B(NOT) enough. It should also be run with a I(validation_type)
        that ensures that the manifest file itself has not changed, such as
        I(validation_type=gpg).
    required: true
    choices:
      - gpg
      - sigstore
      - checksum_manifest
  gpg_pubkey:
    description:
      - The public key to validate a checksum manifest against. Must match the
        detached signature in the project's C(.ansible-sign) directory.
      - Required when I(validation_type=gpg).
  rekor_url:
    description:
      - The URL of the Sigstore Rekor instance the signatures were logged to.
      - Required when I(validation_type=sigstore).
  tuf_url:
    description:
      - The URL of the TUF instance used to retrieve Rekor and Fulcio public keys.
      - Required when I(validation_type=sigstore).
  rekor_root_pubkey:
    description:
      - The PEM public key for the Rekor instance.
      - Required when I(validation_type=sigstore).
  certificate_chain:
    description:
      - Chain of PEM CA certificates to verify the Fulcio signing certificate.
      - Required when I(validation_type=sigstore).
  cert_identity:
    description:
      - The OIDC identity of the signer to look for in the certificate SAN
        (i.e. email address, GitHub Actions workflow).
      - Required when I(validation_type=sigstore).
  oidc_issuer:
    description:
      - The URL of the OIDC provider that issued the signer identity.
      - Required when I(validation_type=sigstore).
  github_trigger:
    description:
      - The GitHub Actions event name that triggered the workflow.
      - Required when I(validation_type=sigstore).
  github_name:
    description:
      - The name of the workflow that was triggered.
      - Required when I(validation_type=sigstore).
  github_repository:
    description:
      - The repository slug that the workflow was triggered under.
      - Required when I(validation_type=sigstore).
  github_ref:
    description:
      - The git ref that the workflow was invoked with.
      - Required when I(validation_type=sigstore).
  verify_offline:
    description:
      - Verify signatures offline (default: False).
      - Required when I(validation_type=sigstore).
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

    - name: Verify project content using Sigstore
      playbook_integrity:
        project_path: /srv/projects/example
        validation_type: sigstore
        rekor_url: "https://rekor.sigstore.dev"
        tuf_url: "https://sigstore-tuf-root.storage.googleapis.com/
        certificate_chain: "{{ certificate_chain }}"
        cert_identity: "jdoe@example.com"
        oidc_issuer: "https://github.com/login/oauth"
        verify_offline: false

    - name: Verify project content against checksum manifest
      playbook_integrity:
        project_path: /srv/projects/example
        validation_type: checksum_manifest
"""
