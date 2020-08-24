#!/bin/sh
set -ue

requirements_in="$(readlink -f ./requirements.in)"
requirements="$(readlink -f ./requirements.txt)"
pip_compile="pip-compile --no-header --quiet -r --allow-unsafe"

check_prerequisites() {
  for thing in patch awk python3 python2 virtualenv ; do
      command -v $thing >/dev/null 2>&1 || { echo "$thing not installed or available. Please fix this before running." ; exit 1 ; }
  done
}

_cleanup() {
  cd /
  test "${KEEP_TMP:-0}" = 1 || rm -rf "${_tmp}"
}

install_deps() {
  pip install pip --upgrade
  pip install pip-tools
}

generate_requirements_v3() {
  venv="./venv3"
  python3 -m venv "${venv}"
  # shellcheck disable=SC1090
  . "${venv}/bin/activate"

  install_deps

  ${pip_compile} --output-file requirements.txt "${requirements_in}"
}

main() {
  check_prerequisites

  _tmp="$(mktemp -d --suffix .awx-requirements XXXX -p /tmp)"
  trap _cleanup INT TERM EXIT

  if [ "$1" = "upgrade" ]; then
      pip_compile="${pip_compile} --upgrade"
  fi

  cd "${_tmp}"

  generate_requirements_v3

  cp -vf requirements.txt "${requirements}"

  _cleanup
}

# set EVAL=1 in case you want to source this script
test "${EVAL:-0}" -eq "1" || main "${1:-}"
