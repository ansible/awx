# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed
from django.db import models
from django.db.models.fields.related import (
    add_lazy_relation,
    SingleRelatedObjectDescriptor,
    ReverseSingleRelatedObjectDescriptor,
    ManyRelatedObjectsDescriptor,
    ReverseManyRelatedObjectsDescriptor,
)

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





class ResourceFieldDescriptor(ReverseSingleRelatedObjectDescriptor):
    """Descriptor for access to the object from its related class."""

    def __init__(self, *args, **kwargs):
        super(ResourceFieldDescriptor, self).__init__(*args, **kwargs)

    def __get__(self, instance, instance_type=None):
        resource = super(ResourceFieldDescriptor, self).__get__(instance, instance_type)
        if resource:
            return resource
        resource = Resource._default_manager.create(content_object=instance)
        setattr(instance, self.field.name, resource)
        instance.save(update_fields=[self.field.name,])
        return resource


class ImplicitResourceField(models.ForeignKey):
    """Creates an associated resource object if one doesn't already exist"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', 'Resource')
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('null', 'True')
        super(ImplicitResourceField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(ImplicitResourceField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ResourceFieldDescriptor(self))
        post_save.connect(self._save, cls, True)

    def _save(self, instance, *args, **kwargs):
        # Ensure that our field gets initialized after our first save
        if not hasattr(instance, self.name):
            getattr(instance, self.name)


class ImplicitRoleDescriptor(ReverseSingleRelatedObjectDescriptor):
    """Descriptor Implict Role Fields. Auto-creates the appropriate role entry on first access"""

    def __init__(self, role_name, permissions, parent_role,  *args, **kwargs):
        self.role_name = role_name
        self.permissions = permissions
        self.parent_role = parent_role

        super(ImplicitRoleDescriptor, self).__init__(*args, **kwargs)

    def __get__(self, instance, instance_type=None):
        role = super(ImplicitRoleDescriptor, self).__get__(instance, instance_type)
        if role:
            return role

        if not self.role_name:
            raise FieldError('Implicit role missing `role_name`')

        role = Role._default_manager.create(name=self.role_name, content_object=instance)
        if self.parent_role:
            def resolve_field(obj, field):
                ret = []

                field_components = field.split('.', 1)
                if hasattr(obj, field_components[0]):
                    obj = getattr(obj, field_components[0])
                else:
                    return []

                if len(field_components) == 1:
                    if type(obj) is not ImplicitRoleDescriptor and type(obj) is not Role:
                        raise Exception('%s refers to a %s, not an ImplicitRoleField or Role' % (field, str(type(obj))))
                    ret.append(obj)
                else:
                    if type(obj) is ManyRelatedObjectsDescriptor:
                        for o in obj.all():
                            ret += resolve_field(o, field_components[1])
                    else:
                        ret += resolve_field(obj, field_components[1])

                return ret

            # Add all non-null parent roles as parents
            paths = self.parent_role if type(self.parent_role) is list else [self.parent_role]
            for path in paths:
                if path.startswith("singleton:"):
                    parents = [Role.singleton(path[10:])]
                else:
                    parents = resolve_field(instance, path)
                for parent in parents:
                    role.parents.add(parent)
        setattr(instance, self.field.name, role)
        instance.save(update_fields=[self.field.name,])

        if self.permissions is not None:
            permissions = RolePermission(
                role=role,
                resource=instance.resource
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

    def __init__(self, role_name=None, permissions=None, parent_role=None, *args, **kwargs):
        self.role_name = role_name
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
                    self.permissions,
                    self.parent_role,
                    self
                )
                )
        post_save.connect(self._save, cls, True)
        add_lazy_relation(cls, self, "self", self.bind_m2m_changed)

    def bind_m2m_changed(self, _self, _role_class, cls):
        if not self.parent_role:
            return
        field_names = self.parent_role
        if type(field_names) is not list:
            field_names = [field_names]

        found_m2m_field = False
        for field_name in field_names:
            if field_name.startswith('singleton:'):
                continue

            first_field_name = field_name.split('.')[0]
            field = getattr(cls, first_field_name)

            if type(field) is ReverseManyRelatedObjectsDescriptor or \
               type(field) is ManyRelatedObjectsDescriptor:
                if found_m2m_field:
                    # This limitation is due to a lack of understanding on my part, the
                    # trouble being that I can't seem to get m2m_changed to call anything that
                    # encapsulates what field we're working with. So the workaround that I've
                    # settled on for the time being is to simply iterate over the fields in the
                    # m2m_update and look for the m2m map and update accordingly. This solution
                    # is lame, I'd love for someone to show me the way to get the necessary
                    # state down to the m2m_update callback. - anoek 2016-02-10
                    raise Exception('Multiple ManyToMany fields not allowed in parent_role list')
                if len(field_name.split('.')) != 2:
                    raise Exception('Referencing deep roles through ManyToMany fields is unsupported.')

                found_m2m_field = True
                self.m2m_field_name = first_field_name
                self.m2m_field_attr = field_name.split('.',1)[1]

                if type(field) is ReverseManyRelatedObjectsDescriptor:
                    m2m_changed.connect(self.m2m_update, field.through)
                else:
                    m2m_changed.connect(self.m2m_update_related, field.related.through)


    def m2m_update_related(self, **kwargs):
        kwargs['reverse'] = not kwargs['reverse']
        self.m2m_update(**kwargs)

    def m2m_update(self, sender, instance, action, reverse, model, pk_set, **kwargs):
        if action == 'post_add' or action == 'pre_remove':
            if reverse:
                for pk in pk_set:
                    obj = model.objects.get(pk=pk)
                    if action == 'post_add':
                        getattr(instance, self.name).children.add(getattr(obj, self.m2m_field_attr))
                    if action == 'pre_remove':
                        getattr(instance, self.name).children.remove(getattr(obj, self.m2m_field_attr))

            else:
                for pk in pk_set:
                    obj = model.objects.get(pk=pk)
                    if action == 'post_add':
                        getattr(instance, self.name).parents.add(getattr(obj, self.m2m_field_attr))
                    if action == 'pre_remove':
                        getattr(instance, self.name).parents.remove(getattr(obj, self.m2m_field_attr))


    def _save(self, instance, *args, **kwargs):
        # Ensure that our field gets initialized after our first save
        if not hasattr(instance, self.name):
            getattr(instance, self.name)
