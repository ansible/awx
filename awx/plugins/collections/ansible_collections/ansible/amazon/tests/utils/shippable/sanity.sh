#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

group="${args[1]}"

if [ "${BASE_BRANCH:-}" ]; then
    base_branch="origin/${BASE_BRANCH}"
else
    base_branch=""
fi

case "${group}" in
    1) options=(--skip-test pylint --skip-test ansible-doc --skip-test validate-modules) ;;
    2) options=(                   --test      ansible-doc) ;;
    3) options=(--test pylint --exclude test/units/ --exclude lib/ansible/module_utils/) ;;
    4) options=(--test pylint           test/units/           lib/ansible/module_utils/) ;;
    5) options=(                                                                                                --test validate-modules) ;;
esac

# shellcheck disable=SC2086
ansible-test sanity --color -v --junit ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    --docker --base-branch "${base_branch}" \
    "${options[@]}" --allow-disabled
