#!/bin/sh
set -ue

requirements_in="$(readlink -f ./requirements.in)"
requirements_ansible_in="$(readlink -f ./requirements_ansible.in)"
requirements="$(readlink -f ./requirements.txt)"
requirements_git="$(readlink -f ./requirements_git.txt)"
requirements_ansible="$(readlink -f ./requirements_ansible.txt)"
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

  ${pip_compile} --output-file requirements.txt "${requirements_in}" "${requirements_git}"
  # consider the git requirements for purposes of resolving deps
  # Then remove any git+ lines from requirements.txt
  cp requirements.txt requirements_tmp.txt
  grep -v "^git+" requirements_tmp.txt > requirements.txt && rm requirements_tmp.txt
  ${pip_compile} --output-file requirements_ansible_py3.txt "${requirements_ansible_in}"
}

generate_requirements_v2() {
  venv="./venv2"
  virtualenv -p python2 "${venv}"
  # shellcheck disable=SC1090
  PS1="" . "${venv}/bin/activate"

  install_deps

  ${pip_compile} --output-file requirements_ansible.txt "${requirements_ansible_in}"
}

generate_patch() {
  a="requirements_ansible_py3.txt"
  b="requirements_ansible.txt"
  replace='; python_version < "3" #'

  # most elegant/quick solution I could come up for now
  out="$(diff --ignore-matching-lines='^#' --unified "${a}" "${b}" | \
    awk -v replace="${replace}" '{ if (/^+\w/){ $2=replace; print;} else print; }' | \
    sed 's/ ;/;/g')"
  test -n "${out}"
  echo "${out}"
}

main() {
  check_prerequisites

  _tmp="$(mktemp -d --suffix .awx-requirements XXXX -p /tmp)"
  trap _cleanup INT TERM EXIT

  if [ "$1" = "upgrade" ]; then
      pip_compile="${pip_compile} --upgrade"
  fi

  cp -vf requirements.txt requirements_ansible.txt "${_tmp}"
  cp -vf requirements_ansible.txt "${_tmp}/requirements_ansible_py3.txt"

  cd "${_tmp}"

  generate_requirements_v3
  generate_requirements_v2

  sed -i 's/^wheel==0.30.0.*/wheel==0.33.6  # via azure-cli-core (overriden, see upgrade blockers)/g' requirements_ansible.txt
  sed -i 's/^wheel==0.30.0.*/wheel==0.33.6  # via azure-cli-core (overriden, see upgrade blockers)/g' requirements_ansible_py3.txt
  generate_patch | patch -p4 requirements_ansible_py3.txt

  cp -vf requirements_ansible_py3.txt "${requirements_ansible}"
  cp -vf requirements.txt "${requirements}"

  _cleanup
}

# set EVAL=1 in case you want to source this script
test "${EVAL:-0}" -eq "1" || main "${1:-}"
