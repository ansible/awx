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
from importlib.resources import files

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

            collections_print[candidate.fqcn] = collection_print

        ansible_data = {'installed_collections': collections_print, 'ansible_version': __version__}

        write_path = os.path.join(artifact_dir, 'ansible_data.json')
        with open(write_path, "w") as fd:
            fd.write(json.dumps(ansible_data, indent=2))

        super().v2_playbook_on_stats(stats)
