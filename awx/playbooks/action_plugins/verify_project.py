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
from ansible_sign.signing import GPGVerifier

display = Display()


VALIDATION_TYPES = (
    "checksum_manifest",
    "gpg",
)


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
