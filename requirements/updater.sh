#!/bin/sh
set -ue

requirements_in="$(readlink -f ./requirements.in)"
requirements="$(readlink -f ./requirements.txt)"
requirements_git="$(readlink -f ./requirements_git.txt)"
pip_compile="pip-compile --no-header --quiet -r --allow-unsafe"

_cleanup() {
  cd /
  test "${KEEP_TMP:-0}" = 1 || rm -rf "${_tmp}"
}

generate_requirements() {
  venv="`pwd`/venv"
  echo $venv
  /usr/bin/python3.8 -m venv "${venv}"
  # shellcheck disable=SC1090
  source ${venv}/bin/activate

  ${venv}/bin/python3.8 -m pip install -U pip pip-tools

  ${pip_compile} --output-file requirements.txt "${requirements_in}" "${requirements_git}"
  # consider the git requirements for purposes of resolving deps
  # Then remove any git+ lines from requirements.txt
  cp requirements.txt requirements_tmp.txt
  grep -v "^git+" requirements_tmp.txt > requirements.txt && rm requirements_tmp.txt
}

main() {
  _tmp="$(mktemp -d --suffix .awx-requirements XXXX -p /tmp)"
  trap _cleanup INT TERM EXIT

  if [ "$1" = "upgrade" ]; then
      pip_compile="${pip_compile} --upgrade"
  fi

  cp -vf requirements.txt "${_tmp}"
  cd "${_tmp}"

  generate_requirements

  cp -vf requirements.txt "${requirements}"

  _cleanup
}

# set EVAL=1 in case you want to source this script
test "${EVAL:-0}" -eq "1" || main "${1:-}"
