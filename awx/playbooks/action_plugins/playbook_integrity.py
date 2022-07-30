from __future__ import absolute_import, division, print_function

__metaclass__ = type

import base64
import git
import gnupg
import hashlib
import os
import tempfile
import traceback
from ansible.module_utils.basic import *
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display


display = Display()


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False

        result = super(ActionModule, self).run(tmp, task_vars)

        params = self._task.args

        scm_type = params.get("scm_type")
        if scm_type is None:
            return {
                "failed": True,
                "msg": "scm_type not given, needed for checksum verification.",
            }

        differ_cls = SCM_FILE_EXISTENCE_CHECKER_MAP.get(scm_type)
        if differ_cls is None:
            return {
                "failed": True,
                "msg": "scm_type given is not supported.",
            }

        project_path = params.get("project_path")
        if project_path is None:
            return {
                "failed": True,
                "msg": "No project path (project_path) was supplied.",
            }

        sig_type = params.get("sig_type")
        if sig_type is None:
            return {
                "failed": True,
                "msg": "No signature type (sig_type) was supplied. Try setting it to 'gpg'?",
            }

        sig_verifier_cls = SIGNATURE_VALIDATION_MAP.get(sig_type)
        if sig_verifier_cls is None:
            return {
                "failed": True,
                "msg": f"sig_type given is not supported, must be one of: {', '.join(SIGNATURE_VALIDATION_MAP.keys())}",
            }

        # NOTE: We currently do checksum validation before we do signature
        # verification. We should probably flip them because the former takes
        # more work, and if the signature check fails, there's no sense
        # in doing that extra work.

        # The validator will assume that the directory containing the checksum
        # file is the root of the project.
        checksum_path = os.path.join(project_path, "sha256sum.txt")
        validator = ChecksumFileValidator.from_path(checksum_path, differ=differ_cls)

        # Do checksum validation
        try:
            validator.verify()
        except InvalidChecksumLine as e:
            return {
                "failed": True,
                "msg": f"Checksum file contained a line that could not be parsed: {e}",
            }
        except ChecksumMismatch as e:
            return {
                "failed": True,
                "msg": f"Checksum validation failed: {e}",
            }

        # Do signature validation
        verifier = sig_verifier_cls(params)
        verification = verifier.verify()
        result.update(verification)
        return result


class ContentVerifier:
    '''
    Represents a way of performing content verification. It doesn't make any
    assumptions about the kind of verification being done. The constructor takes
    raw parameters from the action, and subclasses can make use of those as
    needed to perform whatever kind of verification they want to.
    '''

    def __init__(self, params):
        self.params = params

    def verify(self):
        '''
        Does the actual verification.
        '''
        raise NotImplementedError("verify")


class GPGVerifier(ContentVerifier):
    def __init__(self, params):
        super(GPGVerifier, self).__init__(params)
        self.pubkey = params.get("gpg_pubkey")

        # We know this key exists, because we check for it before we do checksum
        # validation.
        self.project_path = params.get("project_path")

    def verify(self):
        if self.pubkey is None:
            return {
                "failed": True,
                "msg": "No GPG public key (gpg_pubkey) was supplied.",
            }

        sha256sum_path = os.path.join(self.project_path, "sha256sum.txt")
        sha256sum_sig_path = f"{sha256sum_path}.sig"

        if not os.path.exists(sha256sum_sig_path):
            return {
                "failed": True,
                "msg": "Project path existed but did not contain 'sha256sum.txt.sig'.",
            }

        result = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            gpg = gnupg.GPG(gnupghome=tmpdir)
            import_result = gpg.import_keys(self.pubkey)
            result["gpg_pubkeys_imported"] = import_result.count
            result["gpg_fingerprints"] = import_result.fingerprints

            with open(sha256sum_sig_path, 'rb') as sha256sum_sig:
                verified = gpg.verify_file(sha256sum_sig, sha256sum_path)

            if not verified:
                return {
                    "failed": True,
                    "msg": "Verification of checksum file failed.",
                    "details": {
                        "gpg_stderr": verified.stderr,
                    },
                }

            return {
                "failed": False,
                "msg": "Verification of checksum file succeeded.",
                "details": {
                    "gpg_stderr": verified.stderr,
                    "gpg_fingerprint": verified.fingerprint,
                    "gpg_creation_date": verified.creation_date,
                    "gpg_status": verified.status,
                    "gpg_timestamp": verified.timestamp,
                    # "gpg_expiry": verified.expiry,
                },
            }


class ChecksumFileExistenceDiffer:
    '''
    When checking checksum files, it can be important to ensure not only that
    the files listed have correct hashes, but that no files were added that
    are not listed.

    This is particularly important in situations where files might get
    "wildcard-included" -- whereby an extra file slipping in could present a
    security risk.

    This class, and subclasses of it, provide an implementation that
    ChecksumFileValidator instances can use to list all "interesting" files that
    should be listed in the checksum file.
    '''

    ignored_files = set(
        [
            "sha256sum.txt",
            "sha256sum.txt.sig",
        ]
    )

    def __init__(self, root):
        self.root = root
        self.files = self.gather_files()

    def gather_files(self):
        return set()

    def list_files(self):
        return self.files - self.ignored_files

    def compare_filelist(self, checksum_paths):
        '''
        Given a set of paths (from a checksum file), see if files have since
        been added or removed from the root directory and any deeper
        directories.

        The given set of paths is used as the source of truth and additions
        and deletions are list with respect to it.
        '''

        out = {
            "added": set(),
            "removed": set(),
        }
        real_paths = self.list_files()
        out["added"] = real_paths - checksum_paths
        out["removed"] = checksum_paths - real_paths
        return out


class GitChecksumFileExistenceDiffer(ChecksumFileExistenceDiffer):
    '''
    Use gitpython to get walk the file tree of a git repository at HEAD of the
    branch that is currently checked out.
    '''

    def gather_files(self):
        repo = git.Repo(self.root)
        files = set()
        stack = [repo.head.commit.tree]
        while stack:
            tree = stack.pop()
            for blob in tree.blobs:
                files.add(blob.path)
            for inner in tree.trees:
                stack.append(inner)
        return set(files)


class InvalidChecksumLine(Exception):
    pass


class NoDifferException(Exception):
    pass


class ChecksumMismatch(Exception):
    pass


class ChecksumFileValidator:
    '''
    Slurp a checksum file and be able to check and compare its contents to a
    given root directory.

    We assume sha256 for now.
    '''

    def __init__(self, raw_checksum_file, root, differ=None):
        self._raw_checksum_file = raw_checksum_file
        self.root = root
        if differ is not None:
            self.differ = differ(root=root)
        self.parsed_checksums = self._parse()

    @classmethod
    def from_path(cls, path, *args, **kwargs):
        if not args and "root" not in kwargs:
            kwargs["root"] = os.path.dirname(path)
        return cls(open(path, 'r').read(), *args, **kwargs)

    def _parse_bsd_style(self, line):
        '''
        Attempt to parse a BSD style checksum line, returning False if we
        are unable to.

        A BSD style line looks like this:
        SHA256 (hello_world.yml) = f712979c4c5dfe739253908d122f5c87faa8b5de6f15ba7a1548ae028ff22d13
        '''

        # Each BSD line is prefixed with 'SHA256 ('. Then, starting from the
        # right (and assuming sha256 only, for now) we can count 68
        # characters ( sha length and ") = " ) to look for another pattern.
        if line.startswith('SHA256 (') and line[-68:-64] == ') = ':
            # If both of those criteria match, we are pretty confident this
            # is a BSD style line. From the right, split once at the = sign
            # and parse out the path, and we are done. If the split
            # doesn't work, or the sha isn't length 64, then assume it's
            # not a BSD line, after all.
            parts = line.rsplit(' = ', 1)
            if len(parts) == 2 and len(parts[1]) == 64:
                path = parts[0][8:-1]
                shasum = parts[1]
            return (path, shasum)
        return False

    def _parse_gnu_style(self, line):
        '''
        Attempt to parse a GNU style line checksum line, returning False if
        we are unable to.

        A GNU style line looks like this:
        f712979c4c5dfe739253908d122f5c87faa8b5de6f15ba7a1548ae028ff22d13  hello_world.yml

        Or maybe like this:
        f82da8b4f98a3d3125fbc98408911f65dbc8dc38c0f38e258ebe290a8ad3d3c0 *binary
        '''

        parts = line.split(' ', 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            return False

        if len(parts[1]) < 2 or parts[1][0] not in (' ', '*'):
            return False

        shasum = parts[0]
        path = parts[1][1:]
        return (path, shasum)

    def _parse(self):
        checksums = {}
        for idx, line in enumerate(self._raw_checksum_file.splitlines()):
            if not line.strip():
                continue
            parsed = self._parse_bsd_style(line)
            if parsed is False:
                parsed = self._parse_gnu_style(line)
            if parsed is False:
                raise InvalidChecksumLine(f"Unparsable checksum, line {idx + 1}: {line}")
            path = parsed[0]
            shasum = parsed[1]
            if path in checksums:
                raise InvalidChecksumLine(f"Duplicate path in checksum, line {idx + 1}: {line}")
            checksums[path] = shasum
        return checksums

    def diff(self):
        if self.differ is None:
            raise NoDifferException("diff: No differ was associated with this instance")
        paths = set(self.parsed_checksums.keys())
        return self.differ.compare_filelist(paths)

    def calculate_checksum(self, path):
        fullpath = os.path.join(self.root, path)
        shasum = hashlib.sha256()
        with open(fullpath, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                shasum.update(chunk)
        return shasum.hexdigest()

    def calculate_checksums(self):
        # This uses the paths found in the parsed checksum file.
        # Just calling this is not enough in many cases- you want to ensure that
        # the files in the checksum list are the same ones present in reality.
        # diff() above does just that. Use that in combination with this method,
        # or use verify() which does it for you.
        out = {}
        for path in self.parsed_checksums.keys():
            shasum = self.calculate_checksum(path)
            out[path] = shasum
        return out

    def verify(self):
        # If there are any differences in existing paths, fail the check...
        differences = self.diff()
        if differences["added"] or differences["removed"]:
            raise ChecksumMismatch(differences)

        recalculated = self.calculate_checksums()
        mismatches = set()
        for parsed_path, parsed_checksum in self.parsed_checksums.items():
            if recalculated[parsed_path] != parsed_checksum:
                mismatches.add(parsed_path)
        if mismatches:
            raise ChecksumMismatch(f"Checksum mismatch: {', '.join(mismatches)}")

        return True


SCM_FILE_EXISTENCE_CHECKER_MAP = {
    "git": GitChecksumFileExistenceDiffer,
}

SIGNATURE_VALIDATION_MAP = {
    "gpg": GPGVerifier,
}
