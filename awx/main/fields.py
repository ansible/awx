# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import connection
from django.db.models.signals import (
    post_init,
    pre_save,
    post_save,
    post_delete,
)
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
from django.db.transaction import TransactionManagementError


# AWX
from awx.main.models.rbac import RolePermission, Role, batch_role_ancestor_rebuilding


__all__ = ['AutoOneToOneField', 'ImplicitRoleField']


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






def resolve_role_field(obj, field):
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
                ret += resolve_role_field(o, field_components[1])
        else:
            ret += resolve_role_field(obj, field_components[1])

    return ret


class ImplicitRoleDescriptor(ReverseSingleRelatedObjectDescriptor):
    pass


class ImplicitRoleField(models.ForeignKey):
    """Implicitly creates a role entry for a resource"""

    def __init__(self, role_name=None, role_description=None, permissions=None, parent_role=None, *args, **kwargs):
        self.role_name = role_name
        self.role_description = role_description if role_description else ""
        self.permissions = permissions
        self.parent_role = parent_role

        kwargs.setdefault('to', 'Role')
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('null', 'True')
        super(ImplicitRoleField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(ImplicitRoleField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ImplicitRoleDescriptor(self))

        if not hasattr(cls, '__implicit_role_fields'):
            setattr(cls, '__implicit_role_fields', [])
        getattr(cls, '__implicit_role_fields').append(self)

        post_init.connect(self._post_init, cls, True, dispatch_uid='implicit-role-post-init')
        pre_save.connect(self._pre_save, cls, True, dispatch_uid='implicit-role-pre-save')
        post_save.connect(self._post_save, cls, True, dispatch_uid='implicit-role-post-save')
        post_delete.connect(self._post_delete, cls, True)
        add_lazy_relation(cls, self, "self", self.bind_m2m_changed)

    def bind_m2m_changed(self, _self, _role_class, cls):
        if not self.parent_role:
            return

        field_names = self.parent_role
        if type(field_names) is not list:
            field_names = [field_names]

        for field_name in field_names:
            if field_name.startswith('singleton:'):
                continue

            field_name, sep, field_attr = field_name.partition('.')
            field = getattr(cls, field_name)

            if type(field) is ReverseManyRelatedObjectsDescriptor or \
               type(field) is ManyRelatedObjectsDescriptor:

                if '.' in field_attr:
                    raise Exception('Referencing deep roles through ManyToMany fields is unsupported.')

                if type(field) is ReverseManyRelatedObjectsDescriptor:
                    sender = field.through
                else:
                    sender = field.related.through

                reverse = type(field) is ManyRelatedObjectsDescriptor
                m2m_changed.connect(self.m2m_update(field_attr, reverse), sender, weak=False)

    def m2m_update(self, field_attr, _reverse):
        def _m2m_update(instance, action, model, pk_set, reverse, **kwargs):
            if action == 'post_add' or action == 'pre_remove':
                if _reverse:
                    reverse = not reverse

                if reverse:
                    for pk in pk_set:
                        obj = model.objects.get(pk=pk)
                        if action == 'post_add':
                            getattr(instance, field_attr).children.add(getattr(obj, self.name))
                        if action == 'pre_remove':
                            getattr(instance, field_attr).children.remove(getattr(obj, self.name))

                else:
                    for pk in pk_set:
                        obj = model.objects.get(pk=pk)
                        if action == 'post_add':
                            getattr(instance, self.name).parents.add(getattr(obj, field_attr))
                        if action == 'pre_remove':
                            getattr(instance, self.name).parents.remove(getattr(obj, field_attr))
        return _m2m_update


    def _post_init(self, instance, *args, **kwargs):
        original_parent_roles = dict()
        if instance.pk:
            for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
                original_parent_roles[implicit_role_field.name] = implicit_role_field._resolve_parent_roles(instance)

        setattr(instance, '__original_parent_roles', original_parent_roles)

    def _create_role_instance_if_not_exists(self, instance):
        role = getattr(instance, self.name, None)
        if role:
            return role
        role = Role.objects.create(
                name=self.role_name,
                description=self.role_description)
        setattr(instance, self.name, role)

    def _patch_role_content_object_and_grant_permissions(self, instance):
        role = getattr(instance, self.name)
        role.content_object = instance
        role.save()

        if self.permissions is not None:
            permissions = RolePermission(
                role=role,
                resource=instance,
                auto_generated=True
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

    def _pre_save(self, instance, *args, **kwargs):
        for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
            implicit_role_field._create_role_instance_if_not_exists(instance)

    def _post_save(self, instance, created, *args, **kwargs):
        if created:
            for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
                implicit_role_field._patch_role_content_object_and_grant_permissions(instance)

        original_parent_roles = getattr(instance, '__original_parent_roles')

        if created:
            for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
                original_parent_roles[implicit_role_field.name] = set()

        new_parent_roles = dict()
        for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
            new_parent_roles[implicit_role_field.name] = implicit_role_field._resolve_parent_roles(instance)
        setattr(instance, '__original_parent_roles', new_parent_roles)

        with batch_role_ancestor_rebuilding():
            for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
                cur_role         = getattr(instance, implicit_role_field.name)
                original_parents = original_parent_roles[implicit_role_field.name]
                new_parents      = new_parent_roles[implicit_role_field.name]
                cur_role.parents.remove(*list(original_parents - new_parents))
                cur_role.parents.add(*list(new_parents - original_parents))


    def _resolve_parent_roles(self, instance):
        if not self.parent_role:
            return set()

        paths = self.parent_role if type(self.parent_role) is list else [self.parent_role]
        parent_roles = set()
        for path in paths:
            if path.startswith("singleton:"):
                parents = [Role.singleton(path[10:])]
            else:
                parents = resolve_role_field(instance, path)
            for parent in parents:
                parent_roles.add(parent)
        return parent_roles

    def _post_delete(self, instance, *args, **kwargs):
        this_role = getattr(instance, self.name)
        children = [c for c in this_role.children.all()]
        this_role.delete()
        with batch_role_ancestor_rebuilding():
            for child in children:
                child.rebuild_role_ancestor_list()
