# Copyright 2012 OpenStack Foundation
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

from glanceclient.openstack.common.apiclient import base


class ImageMember(base.Resource):
    def __repr__(self):
        return "<ImageMember %s>" % self._info

    @property
    def id(self):
        return self.member_id

    def delete(self):
        self.manager.delete(self)


class ImageMemberManager(base.ManagerWithFind):
    resource_class = ImageMember

    def get(self, image, member_id):
        image_id = base.getid(image)
        url = '/v1/images/%s/members/%s' % (image_id, member_id)
        resp, body = self.client.get(url)
        member = body['member']
        member['image_id'] = image_id
        return ImageMember(self, member, loaded=True)

    def list(self, image=None, member=None):
        out = []
        if image and member:
            try:
                out.append(self.get(image, member))
            #TODO(bcwaldon): narrow this down to 404
            except Exception:
                pass
        elif image:
            out.extend(self._list_by_image(image))
        elif member:
            out.extend(self._list_by_member(member))
        else:
            #TODO(bcwaldon): figure out what is appropriate to do here as we
            # are unable to provide the requested response
            pass
        return out

    def _list_by_image(self, image):
        image_id = base.getid(image)
        url = '/v1/images/%s/members' % image_id
        resp, body = self.client.get(url)
        out = []
        for member in body['members']:
            member['image_id'] = image_id
            out.append(ImageMember(self, member, loaded=True))
        return out

    def _list_by_member(self, member):
        member_id = base.getid(member)
        url = '/v1/shared-images/%s' % member_id
        resp, body = self.client.get(url)
        out = []
        for member in body['shared_images']:
            member['member_id'] = member_id
            out.append(ImageMember(self, member, loaded=True))
        return out

    def delete(self, image_id, member_id):
        self._delete("/v1/images/%s/members/%s" % (image_id, member_id))

    def create(self, image, member_id, can_share=False):
        """Creates an image."""
        url = '/v1/images/%s/members/%s' % (base.getid(image), member_id)
        body = {'member': {'can_share': can_share}}
        self.client.put(url, data=body)

    def replace(self, image, members):
        memberships = []
        for member in members:
            try:
                obj = {
                    'member_id': member.member_id,
                    'can_share': member.can_share,
                }
            except AttributeError:
                obj = {'member_id': member['member_id']}
                if 'can_share' in member:
                    obj['can_share'] = member['can_share']
            memberships.append(obj)
        url = '/v1/images/%s/members' % base.getid(image)
        self.client.put(url, data={'memberships': memberships})
