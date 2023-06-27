# Project Signing and Verification

Project signing and verification allows project maintainers to sign their
project directory files with GPG and verify them at project-update time in
AWX/Controller.

## Signing

Signing is provided by a CLI tool and library called
[`ansible-sign`](https://github.com/ansible/ansible-sign) which makes use of
`python-gnupg` to ultimately shell out to GPG to do signing. Currently the only
supported end-user use of this tool is as a CLI utility, but it does provide a
somewhat clean API as well for internal use, and we use this in our verification
process in AWX. More on that below.

`ansible-sign` expects a `MANIFEST.in` file (written in valid `distlib.manifest`
format familiar to most Python project maintainers) which lists the files that
should be included and excluded from the signing process.

Internally, there is a concept of "differs", and a differ is what allows us to
know if files have been added or removed along with which files we should care
about signing and verifying. Currently only one is shipped and supported and
that is the `DistlibManifestChecksumFileExistenceDiffer` which uses
`distlib.manifest` to allow our `MANIFEST.in` machinery to work.

At a broad implementation level, `ansible-sign` works like this when it is asked
to sign a project:

* First, it will ask `distlib.manifest` to read in the `MANIFEST.in` file and
  resolve the entries in it to actual file paths. It processes the directives
  one line at a time. We skip lines starting with `#` along with blank lines. We
  also always implicitly include `MANIFEST.in` itself.
* Once all of the `(recursive-)include`-ed files are resolved, it will iterate
  through all of them and calculate sha256sums for all of them. (It does this by
  reading chunks of the file at a time, to avoid reading entire potentially
  large files into memory).
* Now we have a dictionary of 'file path -> checksum', and we can write it out
  to a file. We store the file in `.ansible-sign/sha256sum.txt`. This is called
  the "checksum manifest file" and it has one line per file. It is in standard
  GNU Coreutils `sha256sum` format.
* Once the checksum manifest is written, we sign it. Signing is modular-ish
  (like the "differ" concept) though only GPG is currently supported and
  implemented. GPG signing uses the `GPGSigner` class which internally uses the
  `python-gnupg` library, which itself shells out to `gpg` to sign the
  file. `GPGSigner` takes parameters such as the passphrase, GnuPG home
  directory, private key to use, and so on. By default `gpg` will use the first
  available private signing key found in the user's default keyring. It will
  write out the detached signature to `.ansible-sign/sha256sum.txt.sig`.
* We do some sanity checking such as ensuring that we get a `0` return code
  (indicating success) back from `gpg`.

## Verifying

On the AWX side, we have a `GPG Public Key` credential type that ships with
AWX. This credential type allows the user to paste in a public GPG key, which
should correspond to the private key used to sign the content. The validity and
"realness" of this key is not currently checked.

Once a `GPG Public Key` credential has been created, it can be attached to the
project (this is just a normal FK relationship). If the project has such a
credential associated with it, content verification will be enabled. Otherwise,
it will be skipped.

Project verification happens only during project update, _not_ during Job
launch. There is an action plugin in
`awx/playbooks/action_plugins/verify_project.py` which uses `ansible-sign` as a
library for doing verification. The implementation is similar to the
`ansible-sign project gpg-verify` subcommand; they both use the same library
calls internally. If the API changes, both places will need to be updated.

Verifying reverts the general signing process described above:

* First we ensure a few files exist (the signature file, the manifest file, and
  `MANIFEST.in`).
* We once again use `python-gnupg` (via our `GPGVerifier` class this time) and
  ask it to validate the detached signature. It will check it against keys in
  our public keyring unless we give it another keyring to use instead. (On the
  CLI we can do this with `--keyring`; on the AWX/Controller side, we get a
  fresh keyring every time the EE spawns, so we import the public key from the
  credential and just let it check against the default keyring).
* Once the key is imported, we can use it to verify if the signature corresponds
  to the checksum manifest. `gpg` does this for us (we use `python-gnupg`'s
  `verify_file` method), but effectively it is checking for:
  1. Does the key match up with something known/trusted in our keyring?
  2. Does the signature correspond to the checksum manifest? (In other words,
     has the checksum manifest been modified?)
* After `gpg` tells us everything is okay, the checksum manifest can then be
  used as a "source of truth" for everything else. Our next step is to parse
  checksum manifest file (this is `ChecksumFile#parse`). We'll ultimately have a
  dictionary of `file path -> checksum` after this.
* We then call `ChecksumFile#verify` which internally does a few things:
  1. It will call the differ to parse `MANIFEST.in` again, via
     `ChecksumFile#diff`. We inject an implicit `global-include *` at the top so
     that we catch any files that have been added to the project as
     well. Ultimately `ChecksumFile#diff` will call the differ's
     `compare_filelist` method which takes a list of files (those listed in the
     checksum manifest parsed by `ChecksumFile#parse` a few steps up) and
     compares them against all the files in the project (captured by
     `global-include *`). It returns a dict and groups the results into `added`
     and `removed` keys.
  2. Check the result from above. If there are any files listed in `added` or
     `removed`, we throw `ChecksumMismatch` and bail out early.
  3. Otherwise, no files have been added or removed from the project. In this
     case, we can iterate all the files in the project and take a new checksum
     hash of all of them.
  4. Once we have those, compare those against the parsed manifest file's
     checksums. If there are checksum mismatches, accumulate a list of them and
     raise `ChecksumMismatch`.
