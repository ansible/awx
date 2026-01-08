#!/bin/sh
set -ue

requirements_in="$(readlink -f ./requirements.in)"
requirements="$(readlink -f ./requirements.txt)"
requirements_git="$(readlink -f ./requirements_git.txt)"
requirements_dev="$(readlink -f ./requirements_dev.txt)"
pip_compile="pip-compile --no-header --quiet -r --allow-unsafe"
sanitize_git="1"

_cleanup() {
  cd /
  test "${KEEP_TMP:-0}" = 1 || rm -rf "${_tmp}"
  return 0
}

generate_requirements() {
  local input_reqs="$1"
  venv="$(pwd)/venv"
  echo "$venv"
  /usr/bin/python3.12 -m venv "${venv}"
  # shellcheck disable=SC1090
  source "${venv}/bin/activate"

  # pip version must match the version used in AWX venv (see README.md UPGRADE BLOCKERs)
  "${venv}/bin/python3" -m pip install -U 'pip==25.3' pip-tools

  ${pip_compile} ${input_reqs} --output-file requirements.txt
  # consider the git requirements for purposes of resolving deps
  # Then comment out any git+ lines from requirements.txt
  if [[ "$sanitize_git" == "1" ]] ; then
    while IFS= read -r line; do
      if [[ $line != \#* ]]; then  # ignore lines which are already comments
        # Escape regex special characters for the search pattern
        # Only escape BRE metacharacters: . * ^ $ [ \
        escaped_pattern=$(printf '%s\n' "${line%#*}" | sed 's/[[\.*^$]/\\&/g')
        # Add # to the start of any line matched
        sed -i "s|^.*${escaped_pattern}|# ${line%#*}  # git requirements installed separately|g" requirements.txt
      fi
    done < "${requirements_git}"
  fi;
  return 0
}

main() {
  local command="${1:-}"
  base_dir=$(pwd)
  dest_requirements="${requirements}"
  input_requirements="${requirements_in} ${requirements_git}"

  _tmp=$(python -c "import tempfile; print(tempfile.mkdtemp(suffix='.awx-requirements', dir='/tmp'))")

  trap _cleanup INT TERM EXIT

  case "${command}" in
    "run")
      NEEDS_HELP=0
    ;;
    "dev")
      dest_requirements="${requirements_dev}"
      input_requirements="${requirements_dev}"
      sanitize_git=0
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
      echo "" >&2
      echo "ERROR: Parameter ${command} not valid" >&2
      echo "" >&2
      NEEDS_HELP=1
    ;;
  esac

  if [[ "$NEEDS_HELP" == "1" ]] ; then
    echo "This script generates requirements.txt from requirements.in and requirements_git.in"
    echo "It should be run from within the awx container"
    echo ""
    echo "Usage: $0 [run|upgrade|dev]"
    echo ""
    echo "Commands:"
    echo "help      Print this message"
    echo "run       Run the process only upgrading pinned libraries from requirements.in"
    echo "upgrade   Upgrade all libraries to latest while respecting pinnings"
    echo "dev       Pin the development requirements file"
    echo ""
    exit
  fi

  if [[ ! -d /awx_devel ]] ; then
      echo "This script should be run inside the awx container" >&2
      exit
  fi

  if [[ ! -z "$(tail -c 1 "${requirements_git}")" ]]
  then
      echo "No newline at end of ${requirements_git}, please add one" >&2
      exit
  fi

  cp -vf requirements.txt "${_tmp}"
  cd "${_tmp}"

  generate_requirements "${input_requirements}"

  echo "Changing $base_dir to /awx_devel/requirements"
  cat requirements.txt | sed "s:$base_dir:/awx_devel/requirements:" > "${dest_requirements}"

  _cleanup
  return 0
}

# set EVAL=1 in case you want to source this script
test "${EVAL:-0}" -eq "1" || main "${1:-}"
