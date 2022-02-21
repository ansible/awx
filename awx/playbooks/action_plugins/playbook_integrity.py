from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import platform
import subprocess
from ansible.module_utils.basic import *
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display


display = Display()


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False

        result = super(ActionModule, self).run(tmp, task_vars)

        params = self._task.args

        verifier = Verifier(params)
        try:
            verify_result = verifier.verify()
        except Exception:
            verify_result = {"failed": True}
            verify_result["traceback"] = traceback.format_exc()
        result['detail'] = verify_result
        result['changed'] = True
        return result


TYPE_PLAYBOOK = "playbook"

SIGNATURE_TYPE_GPG = "gpg"
SIGNATURE_TYPE_SIGSTORE = "sigstore"
SIGNATURE_TYPE_SIGSTORE_KEYLESS = "sigstore_keyless"

SIGSTORE_TARGET_TYPE_FILE = "file"

SCM_TYPE_GIT = "git"

DIGEST_FILENAME = "sha256sum.txt"
SIGNATURE_FILENAME_GPG = "sha256sum.txt.sig"
SIGNATURE_FILENAME_SIGSTORE = "sha256sum.txt.sig"

CHECKSUM_OK_IDENTIFIER = ": OK"
TMP_GNUPG_HOME_DIR = "/tmp/gpghome"
TMP_COSIGN_PATH = "/tmp/cosign"


class Verifier:
    def __init__(self, params):
        self.type = params.get("type", "playbook")
        self.target = params.get("target", "")
        if self.target.startswith("~/"):
            self.target = os.path.expanduser(self.target)
        self.signature_type = params.get("signature_type", "gpg")
        self.public_key = params.get("public_key", "")
        self.keyless_signer_id = params.get("keyless_signer_id", "")

    def verify(self):
        result = {}
        if self.type == TYPE_PLAYBOOK:
            result = self.verify_playbook()
        else:
            raise ValueError("type must be one of [{}]".format([TYPE_PLAYBOOK]))
        return result

    def verify_playbook(self):
        result = {"failed": False}
        digester = Digester(self.target)
        result["digest_result"] = digester.check()
        if result["digest_result"]["returncode"] != 0:
            result["failed"] = True
            return result

        if self.signature_type == SIGNATURE_TYPE_GPG:
            result["verify_result"] = self.verify_gpg(self.target, SIGNATURE_FILENAME_GPG, DIGEST_FILENAME, self.public_key)
        elif self.signature_type in [SIGNATURE_TYPE_SIGSTORE, SIGNATURE_TYPE_SIGSTORE_KEYLESS]:
            keyless = True if self.signature_type == SIGNATURE_TYPE_SIGSTORE_KEYLESS else False
            type = SIGSTORE_TARGET_TYPE_FILE
            result["verify_result"] = self.verify_sigstore(self.target, target_type=type, keyless=keyless)
        else:
            raise ValueError("this signature type is not supported: {}".format(self.signature_type))
        if result["verify_result"]["returncode"] != 0:
            result["failed"] = True
            return result

        return result

    def verify_gpg(self, path, sigfile, msgfile, publickey=""):
        if not os.path.exists(path):
            raise ValueError("the directory \"{}\" does not exists".format(path))

        if not os.path.exists(os.path.join(path, sigfile)):
            raise ValueError("signature file \"{}\" does not exists in path \"{}\"".format(sigfile, path))

        gpghome_option = ""
        keyring_option = ""
        if publickey != "":
            try:
                os.makedirs(TMP_GNUPG_HOME_DIR)
            except Exception:
                pass
            gpghome_option = "GNUPGHOME={}".format(TMP_GNUPG_HOME_DIR)
            keyring_option = "--no-default-keyring --keyring {}".format(publickey)
        cmd = "cd {}; {} gpg --verify {} {} {}".format(path, gpghome_option, keyring_option, sigfile, msgfile)
        result = execute_command(cmd)
        return result

    def verify_sigstore(self, target, target_type=SIGSTORE_TARGET_TYPE_FILE, keyless=False):
        result = None
        if target_type == SIGSTORE_TARGET_TYPE_FILE:
            result = self.verify_sigstore_file(self.target, keyless=keyless, msgfile=DIGEST_FILENAME, sigfile=SIGNATURE_FILENAME_SIGSTORE)
        else:
            raise ValueError("this target type \"{}\" is not supported for sigstore signing".format(target_type))
        return result

    def verify_sigstore_file(self, path, keyless=False, msgfile=DIGEST_FILENAME, sigfile=SIGNATURE_FILENAME_SIGSTORE):
        if not os.path.exists(path):
            raise ValueError("the directory \"{}\" does not exists".format(path))

        if not os.path.exists(os.path.join(path, sigfile)):
            raise ValueError("signature file \"{}\" does not exists in path \"{}\"".format(sigfile, path))

        cosign_cmd = get_cosign_path()
        experimental_option = ""
        key_option = ""
        if keyless:
            experimental_option = "COSIGN_EXPERIMENTAL=1"
        else:
            key_option = "--key {}".format(self.public_key)
        cmd = "cd {}; {} {} verify-blob {} --signature {} {}".format(path, experimental_option, cosign_cmd, key_option, sigfile, msgfile)
        result = execute_command(cmd)
        return result


class Digester:
    def __init__(self, path):
        self.path = path
        if path.startswith("~/"):
            self.path = os.path.expanduser(path)
        self.type = self.get_scm_type(path)

    # TODO: implement this
    def get_scm_type(self, path):
        return SCM_TYPE_GIT

    def gen(self, filename=DIGEST_FILENAME):
        result = None
        if self.type == SCM_TYPE_GIT:
            result = self.gen_git(filename=filename)
        else:
            raise ValueError("this SCM type is not supported: {}".format(self.type))
        return result

    def check(self):
        result = self.filename_check()
        if result["returncode"] != 0:
            return result
        result = self.digest_check()
        return result

    def filename_check(self):
        digest_file = os.path.join(self.path, DIGEST_FILENAME)
        if not os.path.exists(digest_file):
            return dict(returncode=1, stdout="", stderr="No such file or directory: {}".format(digest_file))

        tmp_digest_file = os.path.join("/tmp/", DIGEST_FILENAME)
        result = self.gen(filename=tmp_digest_file)
        if result["returncode"] != 0:
            result["stderr"] = "failed to get the current file & digest list.\n\n{}".format(result["stderr"])
        signed_fnames = self.digest_file_to_filename_set(digest_file)
        current_fnames = self.digest_file_to_filename_set(tmp_digest_file)
        if signed_fnames != current_fnames:
            added = current_fnames - signed_fnames if len(current_fnames - signed_fnames) > 0 else None
            removed = signed_fnames - current_fnames if len(signed_fnames - current_fnames) > 0 else None
            result = dict(
                returncode=1,
                stdout="",
                stderr="the following files are detected as differences.\nAdded: {}\nRemoved: {}".format(added, removed),
            )
            return result
        return result

    def digest_file_to_filename_set(self, filename):
        s = set()
        lines = []
        with open(filename, "r") as f:
            lines = f.read()
        for line in lines.splitlines():
            items = line.split(" ")
            fname = items[len(items) - 1]
            s.add(fname)
        return s

    def digest_check(self):
        tmp_check_out = "/tmp/digest_check_output.txt"
        cmd = "cd {}; sha256sum --check {} > {} 2>&1".format(self.path, DIGEST_FILENAME, tmp_check_out)
        result = execute_command(cmd)
        if result["returncode"] != 0:
            check_out_str = ""
            with open(tmp_check_out, "r") as f:
                check_out_str = f.read()
            err_str = result["stderr"]
            for line in check_out_str.splitlines():
                if CHECKSUM_OK_IDENTIFIER in line:
                    continue
                err_str = "{}{}\n".format(err_str, line)
            result["stderr"] = err_str
        return result

    def gen_git(self, filename=DIGEST_FILENAME):
        cmd1 = "cd {}; git ls-tree -r HEAD --name-only | grep -v {}".format(self.path, DIGEST_FILENAME)
        result = execute_command(cmd1)
        if result["returncode"] != 0:
            return result
        raw_fname_list = result["stdout"]
        fname_list = ""
        for line in raw_fname_list.splitlines():
            fpath = os.path.join(self.path, line)
            if os.path.islink(fpath):
                continue
            fname_list = "{}{}\n".format(fname_list, line)
        tmp_fname_list_file = "/tmp/fname_list.txt"
        with open(tmp_fname_list_file, "w") as f:
            f.write(fname_list)
        cmd2 = "cd {}; cat {} | xargs sha256sum > {}".format(self.path, tmp_fname_list_file, filename)
        result = execute_command(cmd2)
        return result


def result_object_to_dict(obj):
    if not isinstance(obj, subprocess.CompletedProcess):
        return {}

    return dict(
        returncode=obj.returncode,
        stdout=obj.stdout,
        stderr=obj.stderr,
    )


def execute_command(cmd="", env_params=None, timeout=None):
    env = None
    if env_params is not None:
        env = os.environ.copy()
        env.update(env_params)
    result = subprocess.run(cmd, shell=True, env=env, timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = result_object_to_dict(result)
    result["command"] = cmd
    return result


def get_cosign_path():
    cmd1 = "command -v cosign"
    result = execute_command(cmd1)
    if result["returncode"] == 0:
        return "cosign"

    if os.path.exists(TMP_COSIGN_PATH):
        return TMP_COSIGN_PATH

    os_name = platform.system().lower()
    machine = platform.uname().machine
    arch = "unknown"
    if machine == "x86_64":
        arch = "amd64"
    elif machine == "aarch64":
        arch = "arm64"
    elif machine == "ppc64le":
        arch = "ppc64le"
    elif machine == "s390x":
        arch = "s390x"
    else:
        arch = machine

    cmd2 = "curl -sL -o {} https://github.com/sigstore/cosign/releases/download/v1.4.1/cosign-{}-{} && chmod +x {}".format(
        TMP_COSIGN_PATH, os_name, arch, TMP_COSIGN_PATH
    )
    result = execute_command(cmd2)
    if result["returncode"] == 0:
        cmd3 = "{} initialize".format(TMP_COSIGN_PATH)
        execute_command(cmd3)
        return TMP_COSIGN_PATH
    else:
        raise ValueError("failed to install cosign command; {}".format(result["stderr"]))
