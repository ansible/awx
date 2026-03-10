#!/bin/bash
# Replace the awx-dot-awx FQCN with ansible.controller across the collection.
#
# This script is run once at the start of every major release branch to
# convert the collection from awx-dot-awx to ansible.controller. The result
# should be committed into the release branch.
#
# Usage:
#   ./awx_collection/tools/replace_fqcn.sh [collection_root]
#
# If collection_root is not provided, defaults to the awx_collection/
# directory relative to this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTION_ROOT="${1:-$(dirname "$SCRIPT_DIR")}"

echo "Replacing FQCN in: $COLLECTION_ROOT"

# Replace namespace and name in galaxy.yml
if [ -f "$COLLECTION_ROOT/galaxy.yml" ]; then
    sed -i 's/^namespace: awx$/namespace: ansible/' "$COLLECTION_ROOT/galaxy.yml"
    sed -i 's/^name: awx$/name: controller/' "$COLLECTION_ROOT/galaxy.yml"
fi

# Replace all FQCN references across the entire collection
# This also converts _COLLECTION_FQCN in controller_api.py, which
# drives _COLLECTION_TYPE and api_path() automatically.
find "$COLLECTION_ROOT" -type f \( -name '*.py' -o -name '*.yml' -o -name '*.yaml' -o -name '*.md' -o -name '*.j2' \) \
    -exec sed -i 's/awx\.awx/ansible.controller/g' {} +

echo "Done."
