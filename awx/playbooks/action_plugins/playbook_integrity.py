from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import platform
import subprocess
import base64
import traceback
import requests
import hashlib
import json
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_public_key
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

DEFAULT_REKOR_URL = "https://rekor.sigstore.dev"
REKOR_API_HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}


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
            tmp_gnupg_home = tempfile.TemporaryDirectory()
            gpghome_option = "GNUPGHOME={}".format(tmp_gnupg_home.name)
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

        msgpath = os.path.join(path, msgfile)
        sigpath = os.path.join(path, sigfile)
        result = verify_cosign_signature(sigpath, msgpath, self.public_key, keyless)
        return result


# This should be replaced with cosign python module once it is ready
def verify_cosign_signature(sigpath, msgpath, pubkeypath, keyless, rekor_url=None):
    result = {}
    msgdata = None
    with open(msgpath, 'rb') as msg_in:
        msgdata = msg_in.read()
    sigdata = None
    with open(sigpath, 'rb') as sig_in:
        sigdata = sig_in.read()
        sigdata = base64.b64decode(sigdata)

    public_key = None
    if keyless:
        hash = hashlib.sha256(msgdata).hexdigest()
        rekord_data = fetch_rekord(rekor_url, hash)
        b64encoded_sigdata_in_rekord = rekord_data.get("spec", {}).get("signature", {}).get("content", "")
        sigdata_in_rekord = base64.b64decode(b64encoded_sigdata_in_rekord)
        if sigdata_in_rekord != sigdata:
            result["returncode"] = 1
            result["stderr"] = "the signature is different from the one in rekor server"
            return result
        b64encoded_cert_pembytes = rekord_data.get("spec", {}).get("signature", {}).get("publicKey", {}).get("content", "")
        cert_pembytes = base64.b64decode(b64encoded_cert_pembytes)
        certificate = x509.load_pem_x509_certificate(cert_pembytes)
        public_key = certificate.public_key()
    else:
        pemlines = None
        with open(pubkeypath, 'rb') as pem_in:
            pemlines = pem_in.read()
        public_key = load_pem_public_key(pemlines)

    try:
        public_key.verify(sigdata, msgdata, ec.ECDSA(hashes.SHA256()))
        result["returncode"] = 0
        result["stdout"] = "the signature has been verified by sigstore python module (a sample module is used here at this moment)"
    except Exception:
        result["returncode"] = 1
        result["stdout"] = "public key type is {}, rekord data: {}".format(type(public_key), json.dumps(rekord_data))
        result["stderr"] = traceback.format_exc()
    return result


# This should be replaced with cosign python module once it is ready
def fetch_rekord(rekor_url, hash):
    if rekor_url is None:
        rekor_url = DEFAULT_REKOR_URL
    rekord_data = None
    rekord_resp = None
    rekor_payload_search = {
        "hash": f"sha256:{hash}",
    }
    payload = json.dumps(rekor_payload_search)
    search_resp = requests.post(f"{rekor_url}/api/v1/index/retrieve", data=payload, headers=REKOR_API_HEADERS)
    uuids = json.loads(search_resp.content)
    uuid = None
    if len(uuids) > 0:
        uuid = uuids[0]
    rekord_resp = requests.get(f"{rekor_url}/api/v1/log/entries/{uuid}", headers=REKOR_API_HEADERS)
    if rekord_resp is None:
        return None

    rekord_resp_data = json.loads(rekord_resp.content)
    b64encoded_rekord = rekord_resp_data[uuid]["body"]
    rekord_data = json.loads(base64.b64decode(b64encoded_rekord))
    return rekord_data


class Digester:
    def __init__(self, path):
        self.path = path
        if path.startswith("~/"):
            self.path = os.path.expanduser(path)
        self.type = self.get_scm_type(path)
        self.tmpdir = tempfile.TemporaryDirectory()

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

        tmp_digest_file = os.path.join(self.tmpdir.name, DIGEST_FILENAME)
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
        tmp_check_out = os.path.join(self.tmpdir.name, "digest_check_output.txt")
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
        tmp_fname_list_file = os.path.join(self.tmpdir.name, "fname_list.txt")
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
