from __future__ import absolute_import, division, print_function

__metaclass__ = type

import gnupg
import os
import tempfile
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

from ansible_sign.checksum import (
    ChecksumFile,
    ChecksumMismatch,
    InvalidChecksumLine,
)
from ansible_sign.checksum.differ import DistlibManifestChecksumFileExistenceDiffer
from ansible_sign.signing import (
    GPGVerifier,
)

from sigstore._internal.ctfe import CTKeyring
from sigstore._internal.tuf import TrustUpdater
from sigstore.errors import Error
from sigstore.transparency import LogEntry
from sigstore.verify import (
    CertificateVerificationFailure,
    LogEntryMissing,
    policy,
    VerificationMaterials,
    Verifier,
)
from sigstore.verify.models import VerificationFailure
from sigstore_protobuf_specs.dev.sigstore.bundle.v1 import Bundle

from cryptography.x509 import load_pem_x509_certificates
from pathlib import Path
from textwrap import dedent


display = Display()


VALIDATION_TYPES = (
    "checksum_manifest",
    "gpg",
    "sigstore",
)
PUBLIC_REKOR_PRODUCTION_URL = "https://rekor.sigstore.dev"
PUBLIC_REKOR_STAGING_URL = "https://rekor.sigstage.dev"


class VerificationError(Error):
    """Raised when the verifier returns a `VerificationFailure` result."""

    def __init__(self, result: VerificationFailure):
        self.message = f"Verification failed: {result.reason}"
        self.result = result

    def diagnostics(self) -> str:
        message = f"Failure reason: {self.result.reason}\n"

        if isinstance(self.result, CertificateVerificationFailure):
            message += dedent(
                f"""
                The given certificate could not be verified against the
                root of trust.

                This may be a result of connecting to the wrong Fulcio instance
                (for example, staging instead of production, or vice versa).

                Additional context:

                {self.result.exception}
                """
            )
        elif isinstance(self.result, LogEntryMissing):
            message += dedent(
                f"""
                These signing artifacts could not be matched to a entry
                in the configured transparency log.

                This may be a result of connecting to the wrong Rekor instance
                (for example, staging instead of production, or vice versa).

                Additional context:

                Signature: {self.result.signature}

                Artifact hash: {self.result.artifact_hash}
                """
            )
        else:
            message += dedent(
                f"""
                A verification error occurred.

                Additional context:

                {self.result}
                """
            )

        return message


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False

        super(ActionModule, self).run(tmp, task_vars)

        self.params = self._task.args

        self.project_path = self.params.get("project_path")
        if self.project_path is None:
            return {
                "failed": True,
                "msg": "No project path (project_path) was supplied.",
            }

        validation_type = self.params.get("validation_type")
        if validation_type is None or validation_type not in VALIDATION_TYPES:
            return {"failed": True, "msg": "validation_type must be one of: " + ', '.join(VALIDATION_TYPES)}
        validation_method = getattr(self, f"validate_{validation_type}")
        return validation_method()

    def validate_gpg(self):
        gpg_pubkey = self.params.get("gpg_pubkey")
        if gpg_pubkey is None:
            return {
                "failed": True,
                "msg": "No GPG public key (gpg_pubkey) was supplied.",
            }

        signature_file = os.path.join(self.project_path, ".ansible-sign", "sha256sum.txt.sig")
        manifest_file = os.path.join(self.project_path, ".ansible-sign", "sha256sum.txt")

        for path in (signature_file, manifest_file):
            if not os.path.exists(path):
                return {
                    "failed": True,
                    "msg": f"Expected file not found: {path}",
                }

        with tempfile.TemporaryDirectory() as gpg_home:
            gpg = gnupg.GPG(gnupghome=gpg_home)
            gpg.import_keys(gpg_pubkey)
            verifier = GPGVerifier(
                manifest_path=manifest_file,
                detached_signature_path=signature_file,
                gpg_home=gpg_home,
            )
            result = verifier.verify()

        return {
            "failed": not result.success,
            "msg": result.summary,
            "gpg_details": result.extra_information,
        }

    def _collect_verification_state(self):
        rekor_url = self.params.get("rekor_url")
        if rekor_url is None:
            return {
                "failed": True,
                "msg": "No Sigstore Rekor instance URL was supplied.",
            }

        self.cert_identity = self.params.get("cert_identity")
        if self.cert_identity is None:
            return {
                "failed": True,
                "msg": "No Sigstore certificate identity was supplied.",
            }

        oidc_issuer = self.params.get("oidc_issuer")
        if oidc_issuer is None:
            return {
                "failed": True,
                "msg": "No Sigstore certificate OIDC issuer was supplied.",
            }

        tuf_url = self.params.get("tuf_url")
        rekor_root_pubkey = self.params.get("rekor_root_pubkey")
        if not (tuf_url or rekor_root_pubkey):
            return {
                "failed": True,
                "msg": "One of Sigstore TUF instance URL or Sigstore Rekor root public key must be supplied.",
            }

        bundle_path = Path(os.path.join(self.project_path, ".ansible-sign", "sha256sum.txt.sigstore"))
        manifest_file_path = Path(os.path.join(self.project_path, ".ansible-sign", "sha256sum.txt"))

        if not manifest_file_path.is_file():
            return {
                "failed": True,
                "msg": f"Expected manifest file not found: {manifest_file_path}",
            }

        if not bundle_path.is_file():
            return {
                "failed": True,
                "msg": f"Sigstore bundle file for signature verification not found: {bundle_path}",
            }

        if self.params.get("staging"):
            verifier = Verifier.staging()
        elif self.params.get("rekor_url") == PUBLIC_REKOR_PRODUCTION_URL:
            verifier = Verifier.production()
        else:
            if not self.params.get("certificate_chain"):
                return {
                    "failed": True,
                    "msg": "Custom Rekor URL used without specifying --certificate-chain",
                }

            try:
                certificate_chain = load_pem_x509_certificates(self.params.get("certificate_chain").read())
            except ValueError as error:
                return {
                    "failed": True,
                    "msg": f"Invalid certificate chain: {error}",
                }

            if self.params.get("rekor_root_pubkey") is not None:
                rekor_key = self.params.get("rekor_root_pubkey").read()
            else:
                updater = TrustUpdater.production()
                rekor_key = updater.get_rekor_key()

            verifier = Verifier(
                rekor=RekorClient(
                    url=self.params.get("rekor_url"),
                    pubkey=rekor_key,
                    # We don't use the CT keyring in verification so we can supply an empty keyring
                    ct_keyring=CTKeyring(),
                ),
                fulcio_certificate_chain=certificate_chain,
            )

        entry: LogEntry | None = None

        bundle_bytes = bundle_path.read_bytes()
        bundle = Bundle().from_json(bundle_bytes)

        with open(manifest_file_path, mode="rb", buffering=0) as io:
            materials = VerificationMaterials.from_bundle(input_=io, bundle=bundle, offline=self.params.get("offline"))
            all_materials = [bundle_path, materials]

        return (verifier, all_materials)

    def validate_sigstore(self):
        verifier, file_with_materials = self._collect_verification_state()
        file, materials = file_with_materials

        if self.cert_identity.startswith("https://github.com"):
            inner_policies: list[policy.VerificationPolicy] = [
                policy.Identity(
                    identity=self.cert_identity,
                    issuer="https://token.actions.githubusercontent.com",
                )
            ]

            github_trigger = self.params.get("github_trigger")
            github_name = self.params.get("github_name")
            github_repo = self.params.get("github_repo")
            github_ref = self.params.get("github_ref")

            if workflow_trigger:
                inner_policies.append(policy.GitHubWorkflowTrigger(workflow_trigger))
            if workflow_name:
                inner_policies.append(policy.GitHubWorkflowName(workflow_name))
            if workflow_repository:
                inner_policies.append(policy.GitHubWorkflowRepository(workflow_repository))
            if workflow_ref:
                inner_policies.append(policy.GitHubWorkflowRef(workflow_ref))

            policy_ = policy.AllOf(inner_policies)

        else:
            policy_ = policy.Identity(
                identity=self.cert_identity,
                issuer=self.params.get("oidc_issuer"),
            )

        result = verifier.verify(
            materials=materials,
            policy=policy_,
        )

        # `result`: sigstore.verify.models.VerificationResult has a custom boolean representation
        if result:
            return {"failed": not result, "msg": f"Sigstore signature verification OK: {file}"}
        else:
            return {"failed": not result, "msg": f"Sigstore signature verification FAILED: {file}. Failure reason: {result.reason}"}

    def validate_checksum_manifest(self):
        checksum = ChecksumFile(self.project_path, differ=DistlibManifestChecksumFileExistenceDiffer)
        manifest_file = os.path.join(self.project_path, ".ansible-sign", "sha256sum.txt")

        if not os.path.exists(manifest_file):
            return {
                "failed": True,
                "msg": f"Expected file not found: {manifest_file}",
            }

        checksum_file_contents = open(manifest_file, "r").read()

        try:
            manifest = checksum.parse(checksum_file_contents)
        except InvalidChecksumLine as e:
            return {
                "failed": True,
                "msg": f"Invalid line in checksum manifest: {e}",
            }

        try:
            checksum.verify(manifest)
        except ChecksumMismatch as e:
            return {
                "failed": True,
                "msg": str(e),
            }

        return {
            "failed": False,
            "msg": "Checksum manifest is valid.",
        }
