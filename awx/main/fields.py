# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db.models.signals import post_save
from django.db import models
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.core.exceptions import FieldError

# AWX
from awx.main.models.rbac import Resource, RolePermission, Role


__all__ = ['AutoOneToOneField', 'ImplicitResourceField', 'ImplicitRoleField']

# Based on AutoOneToOneField from django-annoying:
# https://bitbucket.org/offline/django-annoying/src/a0de8b294db3/annoying/fields.py

class AutoSingleRelatedObjectDescriptor(SingleRelatedObjectDescriptor):
    """Descriptor for access to the object from its related class."""

    def __get__(self, instance, instance_type=None):
        try:
            return super(AutoSingleRelatedObjectDescriptor,
                         self).__get__(instance, instance_type)
        except self.related.related_model.DoesNotExist:
            obj = self.related.related_model(**{self.related.field.name: instance})
            if self.related.field.rel.parent_link:
                raise NotImplementedError('not supported with polymorphic!')
                for f in instance._meta.local_fields:
                    setattr(obj, f.name, getattr(instance, f.name))
            obj.save()
            return obj

class AutoOneToOneField(models.OneToOneField):
    """OneToOneField that creates related object if it doesn't exist."""

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(),
                AutoSingleRelatedObjectDescriptor(related))





def resolve_field(obj, field):
    for f in field.split('.'):
        if hasattr(obj, f):
            obj = getattr(obj, f)
        else:
            obj = None
    return obj

class ResourceFieldDescriptor(ReverseSingleRelatedObjectDescriptor):
    """Descriptor for access to the object from its related class."""

    def __init__(self, parent_resource, *args, **kwargs):
        self.parent_resource = parent_resource
        super(ResourceFieldDescriptor, self).__init__(*args, **kwargs)

    def __get__(self, instance, instance_type=None):
        resource = super(ResourceFieldDescriptor, self).__get__(instance, instance_type)
        if resource:
            return resource
        resource = Resource._default_manager.create()
        if self.parent_resource:
            # Take first non null parent resource
            parent = None
            if type(self.parent_resource) is list:
                for path in self.parent_resource:
                    parent = resolve_field(instance, path)
                    if parent:
                        break
            else:
                parent = resolve_field(instance, self.parent_resource)
            resource.parent = parent
        resource.save()
        setattr(instance, self.field.name, resource)
        instance.save(update_fields=[self.field.name,])
        return resource


class ImplicitResourceField(models.ForeignKey):
    """Creates an associated resource object if one doesn't already exist"""

    def __init__(self, parent_resource=None, *args, **kwargs):
        self.parent_resource = parent_resource
        kwargs.setdefault('to', 'Resource')
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('null', 'True')
        super(ImplicitResourceField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(ImplicitResourceField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ResourceFieldDescriptor(self.parent_resource, self))
        post_save.connect(self._save, cls, True)

    def _save(self, instance, *args, **kwargs):
        # Ensure that our field gets initialized after our first save
        getattr(instance, self.name)


class ImplicitRoleDescriptor(ReverseSingleRelatedObjectDescriptor):
    """Descriptor Implict Role Fields. Auto-creates the appropriate role entry on first access"""

    def __init__(self, role_name, resource_field, permissions, parent_role,  *args, **kwargs):
        self.role_name = role_name
        self.resource_field = resource_field
        self.permissions = permissions
        self.parent_role = parent_role

        super(ImplicitRoleDescriptor, self).__init__(*args, **kwargs)

    def __get__(self, instance, instance_type=None):
        role = super(ImplicitRoleDescriptor, self).__get__(instance, instance_type)
        if role:
            return role

        if not self.role_name:
            raise FieldError('Implicit role missing `role_name`')

        role = Role._default_manager.create(name=self.role_name)
        if self.parent_role:
            # Add all non-null parent roles as parents
            if type(self.parent_role) is list:
                for path in self.parent_role:
                    if path.startswith("singleton:"):
                        parent = Role.singleton(path[10:])
                    else:
                        parent = resolve_field(instance, path)
                    if parent:
                        role.parents.add(parent)
            else:
                if self.parent_role.startswith("singleton:"):
                    parent = Role.singleton(self.parent_role[10:])
                else:
                    parent = resolve_field(instance, self.parent_role)
                if parent:
                    role.parents.add(parent)
        setattr(instance, self.field.name, role)
        instance.save(update_fields=[self.field.name,])

        if self.resource_field and self.permissions:
            permissions = RolePermission(
                role=role,
                resource=getattr(instance, self.resource_field)
            )

            if 'all' in self.permissions and self.permissions['all']:
                del self.permissions['all']
                self.permissions['create']     = True
                self.permissions['read']       = True
                self.permissions['write']      = True
                self.permissions['update']     = True
                self.permissions['delete']     = True
                self.permissions['scm_update'] = True
                self.permissions['use']        = True
                self.permissions['execute']    = True

            for k,v in self.permissions.items():
                setattr(permissions, k, v)
            permissions.save()

        return role


class ImplicitRoleField(models.ForeignKey):
    """Implicitly creates a role entry for a resource"""

    def __init__(self, role_name=None, resource_field=None, permissions=None, parent_role=None, *args, **kwargs):
        self.role_name = role_name
        self.resource_field = resource_field
        self.permissions = permissions
        self.parent_role = parent_role

        kwargs.setdefault('to', 'Role')
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('null', 'True')
        super(ImplicitRoleField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(ImplicitRoleField, self).contribute_to_class(cls, name)
        setattr(cls,
                self.name,
                ImplicitRoleDescriptor(
                    self.role_name,
                    self.resource_field,
                    self.permissions,
                    self.parent_role,
                    self
                )
                )
        post_save.connect(self._save, cls, True)

    def _save(self, instance, *args, **kwargs):
        # Ensure that our field gets initialized after our first save
        getattr(instance, self.name)
