# Copyright (c) 2011 OpenStack Foundation
# All Rights Reserved.
#
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

from cinderclient import base
from cinderclient import utils


class ListExtResource(base.Resource):
    @property
    def summary(self):
        descr = self.description.strip()
        if not descr:
            return '??'
        lines = descr.split("\n")
        if len(lines) == 1:
            return lines[0]
        else:
            return lines[0] + "..."


class ListExtManager(base.Manager):
    resource_class = ListExtResource

    def show_all(self):
        return self._list("/extensions", 'extensions')


@utils.service_type('volume')
def do_list_extensions(client, _args):
    """
    Lists all available os-api extensions.
    """
    extensions = client.list_extensions.show_all()
    fields = ["Name", "Summary", "Alias", "Updated"]
    utils.print_list(extensions, fields)
