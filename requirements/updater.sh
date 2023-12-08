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
  /usr/bin/python3 -m venv "${venv}"
  # shellcheck disable=SC1090
  source ${venv}/bin/activate

  # FIXME: https://github.com/jazzband/pip-tools/issues/1558
  ${venv}/bin/python3 -m pip install -U 'pip<22.0' pip-tools

  ${pip_compile} "${requirements_in}" "${requirements_git}" --output-file requirements.txt
  # consider the git requirements for purposes of resolving deps
  # Then remove any git+ lines from requirements.txt
  while IFS= read -r line; do
    if [[ $line != \#* ]]; then  # ignore comments
      sed -i "\!${line%#*}!d" requirements.txt
    fi
  done < "${requirements_git}"
}

main() {
  base_dir=$(pwd)

  _tmp=$(python -c "import tempfile; print(tempfile.mkdtemp(suffix='.awx-requirements', dir='/tmp'))")

  trap _cleanup INT TERM EXIT

  case $1 in
    "run")
      NEEDS_HELP=0
    ;;
    "upgrade")
      NEEDS_HELP=0
      pip_compile="${pip_compile} --upgrade"
    ;;
    "help")
      NEEDS_HELP=1
    ;;
    *)
      echo ""
      echo "ERROR: Parameter $1 not valid"
      echo ""
      NEEDS_HELP=1
    ;;
  esac

  if [[ "$NEEDS_HELP" == "1" ]] ; then
    echo "This script generates requirements.txt from requirements.in and requirements_git.in"
    echo "It should be run from within the awx container"
    echo ""
    echo "Usage: $0 [run|upgrade]"
    echo ""
    echo "Commands:"
    echo "help      Print this message"
    echo "run       Run the process only upgrading pinned libraries from requirements.in"
    echo "upgrade   Upgrade all libraries to latest while respecting pinnings"
    echo ""
    exit
  fi

  if [[ ! -d /awx_devel ]] ; then
      echo "This script should be run inside the awx container"
      exit
  fi

  if [[ ! -z "$(tail -c 1 "${requirements_git}")" ]]
  then
      echo "No newline at end of ${requirements_git}, please add one"
      exit
  fi

  cp -vf requirements.txt "${_tmp}"
  cd "${_tmp}"

  generate_requirements

  echo "Changing $base_dir to /awx_devel/requirements"
  cat requirements.txt | sed "s:$base_dir:/awx_devel/requirements:" > "${requirements}"

  _cleanup
}

# set EVAL=1 in case you want to source this script
test "${EVAL:-0}" -eq "1" || main "${1:-}"
