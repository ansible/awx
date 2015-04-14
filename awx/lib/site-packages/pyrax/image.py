# -*- coding: utf-8 -*-

# Copyright (c)2014 Rackspace US, Inc.

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

from functools import wraps

import pyrax
from pyrax.object_storage import StorageObject
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


DEFAULT_FORMAT = "vhd"


def assure_image(fnc):
    """
    Converts a image ID passed as the 'image' parameter to a image object.
    """
    @wraps(fnc)
    def _wrapped(self, img, *args, **kwargs):
        if not isinstance(img, Image):
            # Must be the ID
            img = self._manager.get(img)
        return fnc(self, img, *args, **kwargs)
    return _wrapped



class Image(BaseResource):
    """
    This class represents an Image.
    """
    def __init__(self, manager, info, key=None, loaded=False,
            member_manager_class=None, tag_manager_class=None):
        super(Image, self).__init__(manager, info, key=key, loaded=loaded)
        member_manager_class = member_manager_class or ImageMemberManager
        tag_manager_class = tag_manager_class or ImageTagManager
        self._member_manager = member_manager_class(self.manager.api,
                resource_class=ImageMember, response_key="",
                plural_response_key="members", uri_base="images/%s/members" %
                self.id)
        self._tag_manager = tag_manager_class(self.manager.api,
                resource_class=ImageTag, response_key="",
                plural_response_key="tags", uri_base="images/%s/tags" %
                self.id)
        self._non_display = [
                "com.rackspace__1__build_core",
                "com.rackspace__1__build_managed",
                "com.rackspace__1__build_rackconnect",
                "com.rackspace__1__options",
                "com.rackspace__1__platform_target",
                "com.rackspace__1__release_build_date",
                "com.rackspace__1__release_id",
                "com.rackspace__1__release_version",
                "com.rackspace__1__source",
                "com.rackspace__1__visible_core",
                "com.rackspace__1__visible_managed",
                "com.rackspace__1__visible_rackconnect",
                "file",
                "instance_type_ephemeral_gb",
                "instance_type_flavorid",
                "instance_type_id",
                "instance_type_memory_mb",
                "instance_type_name",
                "instance_type_root_gb",
                "instance_type_rxtx_factor",
                "instance_type_swap",
                "instance_type_vcpu_weight",
                "instance_type_vcpus",
                "instance_uuid",
                "org.openstack__1__architecture",
                "org.openstack__1__os_distro",
                "org.openstack__1__os_version",
                "rax_activation_profile",
                "rax_managed",
                "rax_options",
                "schema",
                "self",
                ]


    def update(self, value_dict):
        """
        Accepts a and dictionary of key/value pairs, where the key is an
        attribute of the image, and the value is the desired new value for that
        image.
        """
        return self.manager.update(self, value_dict)


    def change_name(self, newname):
        """
        Image name can be changed via the update() method. This is simply a
        convenience method.
        """
        return self.update({"name": newname})


    def list_members(self):
        """
        Returns a list of all Members for this image.
        """
        return self._member_manager.list()


    def get_member(self, member):
        """
        Returns the ImageMember object representing the specified member
        """
        return self._member_manager.get(member)


    def add_member(self, project_id):
        """
        Adds the project (tenant) represented by the project_id as a member of
        this image.
        """
        return self._member_manager.create(name=None, project_id=project_id)


    def delete_member(self, project_id):
        """
        Removes the project (tenant) represented by the project_id as a member
        of this image.
        """
        return self._member_manager.delete(project_id)


    def add_tag(self, tag):
        """
        Adds the tag to this image.
        """
        return self._tag_manager.add(tag)


    def delete_tag(self, tag):
        """
        Deletes the tag from this image.
        """
        return self._tag_manager.delete(tag)



class ImageMember(BaseResource):
    """
    This class represents a member (user) of an Image.
    """
    @property
    def id(self):
        return self.member_id



class ImageTag(BaseResource):
    """
    This class represents a tag for an Image.
    """
    pass



class ImageTask(BaseResource):
    """
    This class represents a ImageTask.
    """
    pass



class ImageManager(BaseManager):
    """
    Manager class for an Image.
    """
    def _create_body(self, name, metadata=None):
        """
        Used to create the dict required to create a new queue
        """
        if metadata is None:
            body = {}
        else:
            body = {"metadata": metadata}
        return body


    def list(self, limit=None, marker=None, name=None, visibility=None,
            member_status=None, owner=None, tag=None, status=None,
            size_min=None, size_max=None, sort_key=None, sort_dir=None,
            return_raw=False):
        """
        Returns a list of resource objects. Pagination is supported through the
        optional 'marker' and 'limit' parameters. Filtering the returned value
        is possible by specifying values for any of the other parameters.
        """
        uri = "/%s" % self.uri_base
        qs = utils.dict_to_qs(dict(limit=limit, marker=marker, name=name,
                visibility=visibility, member_status=member_status,
                owner=owner, tag=tag, status=status, size_min=size_min,
                size_max=size_max, sort_key=sort_key, sort_dir=sort_dir))
        if qs:
            uri = "%s?%s" % (uri, qs)
        return self._list(uri, return_raw=return_raw)


    def list_all(self, name=None, visibility=None, member_status=None,
            owner=None, tag=None, status=None, size_min=None, size_max=None,
            sort_key=None, sort_dir=None):
        """
        Returns all of the images in one call, rather than in paginated batches.
        """

        def strip_version(uri):
            """
            The 'next' uri contains a redundant version number. We need to
            strip it to use in the method_get() call.
            """
            pos = uri.find("/images")
            return uri[pos:]

        obj_class = self.resource_class
        resp, resp_body = self.list(name=name, visibility=visibility,
                member_status=member_status, owner=owner, tag=tag,
                status=status, size_min=size_min, size_max=size_max,
                sort_key=sort_key, sort_dir=sort_dir, return_raw=True)
        data = resp_body.get(self.plural_response_key, resp_body)
        next_uri = strip_version(resp_body.get("next", ""))
        ret = [obj_class(manager=self, info=res) for res in data if res]
        while next_uri:
            resp, resp_body = self.api.method_get(next_uri)
            data = resp_body.get(self.plural_response_key, resp_body)
            next_uri = strip_version(resp_body.get("next", ""))
            ret.extend([obj_class(manager=self, info=res)
                    for res in data if res])
        return ret


    def create(self, name, img_format=None, img_container_format=None,
            data=None, container=None, obj=None, metadata=None):
        """
        Creates a new image with the specified name. The image data can either
        be supplied directly in the 'data' parameter, or it can be an image
        stored in the object storage service. In the case of the latter, you
        can either supply the container and object names, or simply a
        StorageObject reference.

        You may specify the image and image container formats; if unspecified,
        the default of "vhd" for image format and "bare" for image container
        format will be used.

        NOTE: This is blocking, and may take a while to complete.
        """
        if img_format is None:
            img_format = "vhd"
        if img_container_format is None:
            img_container_format = "bare"
        headers = {
                "X-Image-Meta-name": name,
                "X-Image-Meta-disk_format": img_format,
                "X-Image-Meta-container_format": img_container_format,
                }
        if data:
            img_data = data
        else:
            ident = self.api.identity
            region = self.api.region_name
            clt = ident.get_client("object_store", region)
            if not isinstance(obj, StorageObject):
                obj = clt.get_object(container, obj)
            img_data = obj.fetch()
        uri = "%s/images" % self.uri_base
        resp, resp_body = self.api.method_post(uri, headers=headers,
                data=img_data)



    def update(self, img, value_dict):
        """
        Accepts an image reference (object or ID) and  dictionary of key/value
        pairs, where the key is an attribute of the image, and the value is the
        desired new value for that image.

        NOTE: There is a bug in Glance where the 'add' operation returns a 409
        if the property already exists, which conflicts with the spec. So to
        get around this a fresh copy of the image must be retrieved, and the
        value of 'op' must be determined based on whether this attribute exists
        or not.
        """
        img = self.get(img)
        uri = "/%s/%s" % (self.uri_base, utils.get_id(img))
        body = []
        for key, val in value_dict.items():
            op = "replace" if key in img.__dict__ else "add"
            body.append({"op": op,
                    "path": "/%s" % key,
                    "value": val})
        headers = {"Content-Type":
                "application/openstack-images-v2.1-json-patch"}
        resp, resp_body = self.api.method_patch(uri, body=body, headers=headers)


    def update_image_member(self, img_id, status):
        """
        Updates the image whose ID is given with the status specified. This
        must be called by the user whose project_id is in the members for the
        image. If called by the owner of the image, an InvalidImageMember
        exception will be raised.

        Valid values for 'status' include:
            pending
            accepted
            rejected
        Any other value will result in an InvalidImageMemberStatus exception
        being raised.
        """
        if status not in ("pending", "accepted", "rejected"):
            raise exc.InvalidImageMemberStatus("The status value must be one "
                    "of 'accepted', 'rejected', or 'pending'. Received: '%s'" %
                    status)
        api = self.api
        project_id = api.identity.tenant_id
        uri = "/%s/%s/members/%s" % (self.uri_base, img_id, project_id)
        body = {"status": status}
        try:
            resp, resp_body = self.api.method_put(uri, body=body)
        except exc.NotFound as e:
            raise exc.InvalidImageMember("The update member request could not "
                    "be completed. No member request for that image was found.")



class ImageMemberManager(BaseManager):
    """
    Manager class for members (users) of an Image.
    """
    def _create_body(self, name, project_id):
        """
        Used to create the dict required to add a member to this image.
        """
        body = {"member": project_id}
        return body


    def create(self, name, *args, **kwargs):
        """
        Need to wrap the default call to handle exceptions.
        """
        try:
            return super(ImageMemberManager, self).create(name, *args, **kwargs)
        except Exception as e:
            if e.http_status == 403:
                raise exc.UnsharableImage("You cannot share a public image.")
            else:
                raise



class ImageTagManager(BaseManager):
    """
    Manager class for Image tags.
    """
    def _create_body(self, name):
        """
        Not used; the add() method is used with a PUT request.
        """
        return {}


    def add(self, tag):
        """
        """
        uri = "/%s/%s" % (self.uri_base, tag)
        resp, resp_body = self.api.method_put(uri)



class ImageTasksManager(BaseManager):
    """
    Manager class for ImageTasks.
    """
    def _create_body(self, name, img=None, cont=None, img_format=None,
            img_name=None):
        """
        Used to create a new task. Since tasks don't have names, the required
        'name' parameter is used for the type of task: 'import' or 'export'.
        """
        img = utils.get_id(img)
        cont = utils.get_name(cont)
        body = {"type": name}
        if name == "export":
            body["input"] = {
                    "image_uuid": img,
                    "receiving_swift_container": cont}
        else:
            nm = "%s/%s" % (cont, utils.get_name(img))
            body["input"] = {
                    "image_properties": {"name": img_name or img},
                    "import_from": nm,
                    "import_from_format": img_format or DEFAULT_FORMAT}
        return body


    def create(self, name, *args, **kwargs):
        """
        Standard task creation, but first check for the existence of the
        containers, and raise an exception if they don't exist.
        """
        cont = kwargs.get("cont")
        if cont:
            # Verify that it exists. If it doesn't, a NoSuchContainer exception
            # will be raised.
            api = self.api
            rgn = api.region_name
            cf = api.identity.object_store[rgn].client
            cf.get_container(cont)
        return super(ImageTasksManager, self).create(name, *args, **kwargs)



class JSONSchemaManager(BaseManager):
    """
    Manager class for retrieving JSON schemas.
    """
    def _create_body(self, name):
        """
        Not used.
        """
        pass


    def images(self):
        """
        Returns a json-schema document that represents an image members entity,
        which is a container of image member entities.
        """
        uri = "/%s/images" % self.uri_base
        resp, resp_body = self.api.method_get(uri)
        return resp_body


    def image(self):
        """
        Returns a json-schema document that represents a single image entity.
        """
        uri = "/%s/image" % self.uri_base
        resp, resp_body = self.api.method_get(uri)
        return resp_body


    def image_members(self):
        """
        Returns a json-schema document that represents an image members entity
        (a container of member entities).
        """
        uri = "/%s/members" % self.uri_base
        resp, resp_body = self.api.method_get(uri)
        return resp_body


    def image_member(self):
        """
        Returns a json-schema document that represents an image member entity.
        (a container of member entities).
        """
        uri = "/%s/member" % self.uri_base
        resp, resp_body = self.api.method_get(uri)
        return resp_body


    def image_tasks(self):
        """
        Returns a json-schema document that represents a container of tasks
        entities.
        """
        uri = "/%s/tasks" % self.uri_base
        resp, resp_body = self.api.method_get(uri)
        return resp_body


    def image_task(self):
        """
        Returns a json-schema document that represents an task entity.
        """
        uri = "/%s/task" % self.uri_base
        resp, resp_body = self.api.method_get(uri)
        return resp_body



class ImageClient(BaseClient):
    """
    This is the primary class for interacting with Images.
    """
    name = "Images"


    def _configure_manager(self):
        """
        Create the manager to handle queues.
        """
        self._manager = ImageManager(self, resource_class=Image,
                response_key="", plural_response_key="images",
                uri_base="images")
        self._tasks_manager = ImageTasksManager(self, resource_class=ImageTask,
                response_key="", plural_response_key="tasks",
                uri_base="tasks")
        self._schema_manager = JSONSchemaManager(self, resource_class=None,
                response_key="", plural_response_key="", uri_base="schemas")


    def list(self, limit=None, marker=None, name=None, visibility=None,
            member_status=None, owner=None, tag=None, status=None,
            size_min=None, size_max=None, sort_key=None, sort_dir=None):
        """
        Returns a list of resource objects. Pagination is supported through the
        optional 'marker' and 'limit' parameters. Filtering the returned value
        is possible by specifying values for any of the other parameters.
        """
        return self._manager.list(limit=limit, marker=marker, name=name,
                visibility=visibility, member_status=member_status,
                owner=owner, tag=tag, status=status, size_min=size_min,
                size_max=size_max, sort_key=sort_key, sort_dir=sort_dir)


    def list_all(self, name=None, visibility=None, member_status=None,
            owner=None, tag=None, status=None, size_min=None, size_max=None,
            sort_key=None, sort_dir=None):
        """
        Returns all of the images in one call, rather than in paginated batches.
        The same filtering options available in list() apply here, with the
        obvious exception of limit and marker.
        """
        return self._manager.list_all(name=name, visibility=visibility,
                member_status=member_status, owner=owner, tag=tag,
                status=status, size_min=size_min, size_max=size_max,
                sort_key=sort_key, sort_dir=sort_dir)


    def update(self, img, value_dict):
        """
        Accepts an image reference (object or ID) and  dictionary of key/value
        pairs, where the key is an attribute of the image, and the value is the
        desired new value for that image.
        """
        return self._manager.update(img, value_dict)


    def create(self, name, img_format=None, data=None, container=None,
            obj=None, metadata=None):
        """
        Creates a new image with the specified name. The image data can either
        be supplied directly in the 'data' parameter, or it can be an image
        stored in the object storage service. In the case of the latter, you
        can either supply the container and object names, or simply a
        StorageObject reference.
        """
        return self._manager.create(name, img_format, data=data,
                container=container, obj=obj)


    def change_image_name(self, img, newname):
        """
        Image name can be changed via the update() method. This is simply a
        convenience method.
        """
        return self.update(img, {"name": newname})


    @assure_image
    def list_image_members(self, img):
        """
        Returns a list of members (users) of the specified image.
        """
        return img.list_members()


    @assure_image
    def get_image_member(self, img, member):
        """
        Returns the ImageMember object representing the specified member for the
        specified image.
        """
        return img.get_member(member)


    @assure_image
    def add_image_member(self, img, project_id):
        """
        Adds the project (tenant) represented by the project_id as a member of
        the specified image.
        """
        return img.add_member(project_id)


    @assure_image
    def delete_image_member(self, img, project_id):
        """
        Removes the project (tenant) represented by the project_id as a member
        of the specified image.
        """
        return img.delete_member(project_id)


    def update_image_member(self, img_id, status):
        """
        Updates the image whose ID is given with the status specified. This
        must be called by the user whose project_id is in the members for the
        image; that is, the user with whom the image is being shared. If called
        by the owner of the image, an `InvalidImageMember` exception will be
        raised.

        Valid values for 'status' include:
            pending
            accepted
            rejected

        Any other value will result in an `InvalidImageMemberStatus` exception
        being raised.
        """
        return self._manager.update_image_member(img_id, status)


    @assure_image
    def add_image_tag(self, img, tag):
        """
        Adds the tag to the specified image.
        """
        return img.add_tag(tag)


    @assure_image
    def delete_image_tag(self, img, tag):
        """
        Deletes the tag from the specified image.
        """
        return img.delete_tag(tag)


    def list_tasks(self):
        """
        Returns a list of all tasks.
        """
        return self._tasks_manager.list()


    def get_task(self, task):
        """
        Returns the ImageTask object for the supplied ID.
        """
        return self._tasks_manager.get(task)


    def export_task(self, img, cont):
        """
        Creates a task to export the specified image to the swift container
        named in the 'cont' parameter. If the container does not exist, a
        NoSuchContainer exception is raised.

        The 'img' parameter can be either an Image object or the ID of an
        image. If these do not correspond to a valid image, a NotFound
        exception is raised.
        """
        return self._tasks_manager.create("export", img=img, cont=cont)


    def import_task(self, img, cont, img_format=None, img_name=None):
        """
        Creates a task to import the specified image from the swift container
        named in the 'cont' parameter. The new image will be named the same as
        the object in the container unless you specify a value for the
        'img_name' parameter.

        By default it is assumed that the image is in 'vhd' format; if it is
        another format, you must specify that in the 'img_format' parameter.
        """
        return self._tasks_manager.create("import", img=img, cont=cont,
                img_format=img_format, img_name=img_name)


    def get_images_schema(self):
        """
        Returns a json-schema document that represents an image members entity,
        which is a container of image member entities.
        """
        return self._schema_manager.images()


    def get_image_schema(self):
        """
        Returns a json-schema document that represents a single image entity.
        """
        return self._schema_manager.image()


    def get_image_members_schema(self):
        """
        Returns a json-schema document that represents an image members entity
        (a container of member entities).
        """
        return self._schema_manager.image_members()


    def get_image_member_schema(self):
        """
        Returns a json-schema document that represents an image member entity.
        (a container of member entities).
        """
        return self._schema_manager.image_member()


    def get_image_tasks_schema(self):
        """
        Returns a json-schema document that represents a container of tasks
        entities.
        """
        return self._schema_manager.image_tasks()


    def get_image_task_schema(self):
        """
        Returns a json-schema document that represents an task entity.
        """
        return self._schema_manager.image_task()
