# Copyright 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from novaclient.openstack.common import cliutils
from novaclient import utils


@cliutils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_force_delete(cs, args):
    """Force delete a server."""
    utils.find_resource(cs.servers, args.server).force_delete()


@cliutils.arg('server', metavar='<server>', help='Name or ID of server.')
def do_restore(cs, args):
    """Restore a soft-deleted server."""
    utils.find_resource(cs.servers, args.server).restore()
