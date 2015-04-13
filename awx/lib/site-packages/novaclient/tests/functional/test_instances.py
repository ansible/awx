#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import time
import uuid

import novaclient.client
from novaclient.tests.functional import base


# TODO(sdague): content that probably should be in utils, also throw
# Exceptions when they fail.
def pick_flavor(flavors):
    """Given a flavor list pick a reasonable one."""
    for flavor in flavors:
        if flavor.name == 'm1.tiny':
            return flavor

    for flavor in flavors:
        if flavor.name == 'm1.small':
            return flavor


def pick_image(images):
    for image in images:
        if image.name.startswith('cirros') and image.name.endswith('-uec'):
            return image


def volume_id_from_cli_create(output):
    """Scrape the volume id out of the 'volume create' command

    The cli for Nova automatically routes requests to the volumes
    service end point. However the nova api low level commands don't
    redirect to the correct service endpoint, so for volumes commands
    (even setup ones) we use the cli for magic routing.

    This function lets us get the id out of the prettytable that's
    dumped on the cli during create.

    """
    for line in output.split("\n"):
        fields = line.split()
        if len(fields) > 4:
            if fields[1] == "id":
                return fields[3]


def volume_at_status(output, volume_id, status):
    for line in output.split("\n"):
        fields = line.split()
        if len(fields) > 4:
            if fields[1] == volume_id:
                return fields[3] == status
    raise Exception("Volume %s did not reach status '%s' in output: %s"
                    % (volume_id, status, output))


class TestInstanceCLI(base.ClientTestBase):
    def setUp(self):
        super(TestInstanceCLI, self).setUp()
        # TODO(sdague): while we collect this information in
        # tempest-lib, we do it in a way that's not available for top
        # level tests. Long term this probably needs to be in the base
        # class.
        user = os.environ['OS_USERNAME']
        passwd = os.environ['OS_PASSWORD']
        tenant = os.environ['OS_TENANT_NAME']
        auth_url = os.environ['OS_AUTH_URL']

        # TODO(sdague): we made a lot of fun of the glanceclient team
        # for version as int in first parameter. I guess we know where
        # they copied it from.
        self.client = novaclient.client.Client(
            2, user, passwd, tenant,
            auth_url=auth_url)

        # pick some reasonable flavor / image combo
        self.flavor = pick_flavor(self.client.flavors.list())
        self.image = pick_image(self.client.images.list())

    def test_attach_volume(self):
        """Test we can attach a volume via the cli.

        This test was added after bug 1423695. That bug exposed
        inconsistencies in how to talk to API services from the CLI
        vs. API level. The volumes api calls that were designed to
        populate the completion cache were incorrectly routed to the
        Nova endpoint. Novaclient volumes support actually talks to
        Cinder endpoint directly.

        This would case volume-attach to return a bad error code,
        however it does this *after* the attach command is correctly
        dispatched. So the volume-attach still works, but the user is
        presented a 404 error.

        This test ensures we can do a through path test of: boot,
        create volume, attach volume, detach volume, delete volume,
        destroy.

        """
        # TODO(sdague): better random name
        name = str(uuid.uuid4())

        # Boot via the cli, as we're primarily testing the cli in this test
        self.nova('boot', params="--flavor %s --image %s %s --poll" %
                  (self.flavor.name, self.image.name, name))

        # Be nice about cleaning up, however, use the API for this to avoid
        # parsing text.
        servers = self.client.servers.list(search_opts={"name": name})
        # the name is a random uuid, there better only be one
        self.assertEqual(1, len(servers), servers)
        server = servers[0]
        self.addCleanup(server.delete)

        # create a volume for attachment. We use the CLI because it
        # magic routes to cinder, however the low level API does not.
        volume_id = volume_id_from_cli_create(
            self.nova('volume-create', params="1"))
        self.addCleanup(self.nova, 'volume-delete', params=volume_id)

        # allow volume to become available
        for x in xrange(60):
            volumes = self.nova('volume-list')
            if volume_at_status(volumes, volume_id, 'available'):
                break
            time.sleep(1)
        else:
            self.fail("Volume %s not available after 60s" % volume_id)

        # attach the volume
        self.nova('volume-attach', params="%s %s" % (name, volume_id))

        # volume needs to transition to 'in-use' to be attached
        for x in xrange(60):
            volumes = self.nova('volume-list')
            if volume_at_status(volumes, volume_id, 'in-use'):
                break
            time.sleep(1)
        else:
            self.fail("Volume %s not attached after 60s" % volume_id)

        # clean up on success
        self.nova('volume-detach', params="%s %s" % (name, volume_id))
