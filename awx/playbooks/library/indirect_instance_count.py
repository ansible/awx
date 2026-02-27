# (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = '''
    callback: host_query
    type: notification
    short_description: for demo of indirect host data and counting, this produces collection data
    version_added: historical
    description:
      - Saves collection data to artifacts folder
    requirements:
     - Whitelist in configuration
     - Set AWX_ISOLATED_DATA_DIR, AWX will do this
'''

import os
import json
import re
from importlib.resources import files

from packaging.version import Version, InvalidVersion

from ansible.plugins.callback import CallbackBase

# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.


# Taken from https://github.com/ansible/ansible/blob/devel/lib/ansible/cli/galaxy.py#L1624

from ansible.cli.galaxy import with_collection_artifacts_manager
from ansible.release import __version__

from ansible.galaxy.collection import find_existing_collections
from ansible.utils.collection_loader import AnsibleCollectionConfig
import ansible.constants as C


@with_collection_artifacts_manager
def list_collections(artifacts_manager=None):
    artifacts_manager.require_build_metadata = False

    default_collections_path = set(C.COLLECTIONS_PATHS)
    collections_search_paths = default_collections_path | set(AnsibleCollectionConfig.collection_paths)
    collections = list(find_existing_collections(list(collections_search_paths), artifacts_manager, dedupe=False))
    return collections


# External query path constants
EXTERNAL_QUERY_COLLECTION = 'ansible_collections.redhat.indirect_accounting'
EXTERNAL_QUERY_PATH = 'extensions/audit/external_queries'


def list_external_queries(namespace, name):
    """List all available external query versions for a collection.

    Returns a list of Version objects for all available query files
    matching the namespace.name pattern.
    """
    versions = []

    try:
        queries_dir = files(EXTERNAL_QUERY_COLLECTION) / 'extensions' / 'audit' / 'external_queries'
    except ModuleNotFoundError:
        return versions

    # Pattern: namespace.name.X.Y.Z.yml where X.Y.Z is the version
    pattern = re.compile(rf'^{re.escape(namespace)}\.{re.escape(name)}\.(.+)\.yml$')

    for query_file in queries_dir.iterdir():
        match = pattern.match(query_file.name)
        if match:
            version_str = match.group(1)
            try:
                versions.append(Version(version_str))
            except InvalidVersion:
                # Skip files with invalid version strings
                pass

    return versions


def find_external_query_with_fallback(namespace, name, installed_version, display=None):
    """Find external query file with semantic version fallback.

    Args:
        namespace: Collection namespace (e.g., 'community')
        name: Collection name (e.g., 'vmware')
        installed_version: Version string of installed collection (e.g., '4.5.0')
        display: Ansible display object for logging

    Returns:
        Tuple of (query_content, fallback_used, fallback_version) or (None, False, None)
        - query_content: The query file content if found
        - fallback_used: True if a fallback version was used instead of exact match
        - fallback_version: The version string used (for logging)
    """
    try:
        installed_version_object = Version(installed_version)
    except InvalidVersion:
        # Invalid version string - can't do version comparison
        return None, False, None
    try:
        queries_dir = files(EXTERNAL_QUERY_COLLECTION) / 'extensions' / 'audit' / 'external_queries'
    except ModuleNotFoundError:
        return None, False, None

    # 1. Try exact version match first (AC5.2)
    exact_file = queries_dir / f'{namespace}.{name}.{installed_version}.yml'
    if exact_file.exists():
        with exact_file.open('r') as f:
            return f.read(), False, installed_version

    # 2. Find compatible fallback (same major version, nearest lower version)
    available_versions = list_external_queries(namespace, name)
    if not available_versions:
        return None, False, None
    # Filter to same major version and versions <= installed version (AC5.3, AC5.5)
    compatible_versions = [v for v in available_versions if v.major == installed_version_object.major and v <= installed_version_object]
    if not compatible_versions:
        # No compatible fallback exists (AC5.7)
        return None, False, None
    # Select nearest lower version - highest compatible version (AC5.4)
    fallback_version_object = max(compatible_versions)
    fallback_version_str = str(fallback_version_object)
    fallback_file = queries_dir / f'{namespace}.{name}.{fallback_version_str}.yml'
    if fallback_file.exists():
        with fallback_file.open('r') as f:
            return f.read(), True, fallback_version_str

    return None, False, None


class CallbackModule(CallbackBase):
    """
    logs playbook results, per host, in /var/log/ansible/hosts
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'indirect_instance_count'
    CALLBACK_NEEDS_WHITELIST = True

    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    MSG_FORMAT = "%(now)s - %(category)s - %(data)s\n\n"

    def v2_playbook_on_stats(self, stats):
        artifact_dir = os.getenv('AWX_ISOLATED_DATA_DIR')
        if not artifact_dir:
            raise RuntimeError('Only suitable in AWX, did not find private_data_dir')

        collections_print = {}
        # Loop over collections, from ansible-core these are Candidate objects
        for candidate in list_collections():
            collection_print = {
                'version': candidate.ver,
            }

            query_file = files(f'ansible_collections.{candidate.namespace}.{candidate.name}') / 'extensions' / 'audit' / 'event_query.yml'
            if query_file.exists():
                with query_file.open('r') as f:
                    collection_print['host_query'] = f.read()
                self._display.vv(f"Using embedded query for {candidate.fqcn} v{candidate.ver}")
            else:
                # 2. Check for external query file with version fallback
                query_content, fallback_used, version_used = find_external_query_with_fallback(candidate.namespace, candidate.name, candidate.ver)
                if query_content:
                    collection_print['host_query'] = query_content
                    if fallback_used:
                        # AC5.6: Log when fallback is used
                        self._display.v(f"Using external query {version_used} for {candidate.fqcn} v{candidate.ver}.")
                    else:
                        self._display.v(f"Using external query for {candidate.fqcn} v{candidate.ver}")

            collections_print[candidate.fqcn] = collection_print

        ansible_data = {'installed_collections': collections_print, 'ansible_version': __version__}

        write_path = os.path.join(artifact_dir, 'ansible_data.json')
        with open(write_path, "w") as fd:
            fd.write(json.dumps(ansible_data, indent=2))

        super().v2_playbook_on_stats(stats)
