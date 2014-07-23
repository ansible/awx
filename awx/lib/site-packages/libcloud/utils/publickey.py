# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import hashlib

from libcloud.utils.py3 import hexadigits
from libcloud.utils.py3 import bchr

__all__ = [
    'get_pubkey_openssh_fingerprint',
    'get_pubkey_ssh2_fingerprint',
    'get_pubkey_comment'
]

try:
    from Crypto.Util.asn1 import DerSequence, DerObject
    from Crypto.PublicKey.RSA import algorithmIdentifier, importKey
    pycrypto_available = True
except ImportError:
    pycrypto_available = False


def _to_md5_fingerprint(data):
    hashed = hashlib.md5(data).digest()
    return ":".join(hexadigits(hashed))


def get_pubkey_openssh_fingerprint(pubkey):
    # We import and export the key to make sure it is in OpenSSH format
    if not pycrypto_available:
        raise RuntimeError('pycrypto is not available')
    k = importKey(pubkey)
    pubkey = k.exportKey('OpenSSH')[7:]
    decoded = base64.decodestring(pubkey)
    return _to_md5_fingerprint(decoded)


def get_pubkey_ssh2_fingerprint(pubkey):
    # This is the format that EC2 shows for public key fingerprints in its
    # KeyPair mgmt API
    if not pycrypto_available:
        raise RuntimeError('pycrypto is not available')
    k = importKey(pubkey)
    derPK = DerSequence([k.n, k.e])
    bitmap = DerObject('BIT STRING')
    bitmap.payload = bchr(0x00) + derPK.encode()
    der = DerSequence([algorithmIdentifier, bitmap.encode()])
    return _to_md5_fingerprint(der.encode())


def get_pubkey_comment(pubkey, default=None):
    if pubkey.startswith("ssh-"):
        # This is probably an OpenSSH key
        return pubkey.strip().split(' ', 3)[2]
    if default:
        return default
    raise ValueError('Public key is not in a supported format')
