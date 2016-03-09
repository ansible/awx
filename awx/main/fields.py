# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import connection
from django.db.models.signals import (
    post_init,
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
from awx.main.models.rbac import RolePermission, Role


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
    """Descriptor Implict Role Fields. Auto-creates the appropriate role entry on first access"""

    def __init__(self, role_name, role_description, permissions, parent_role,  *args, **kwargs):
        self.role_name = role_name
        self.role_description = role_description if role_description else ""
        self.permissions = permissions
        self.parent_role = parent_role

        super(ImplicitRoleDescriptor, self).__init__(*args, **kwargs)

    def __get__(self, instance, instance_type=None):
        role = super(ImplicitRoleDescriptor, self).__get__(instance, instance_type)
        if role:
            return role

        if not self.role_name:
            raise FieldError('Implicit role missing `role_name`')

        if connection.needs_rollback:
            raise TransactionManagementError('Current transaction has failed, cannot create implicit role')


        role = Role.objects.create(name=self.role_name, description=self.role_description, content_object=instance)
        setattr(instance, self.field.name, role)
        if instance.pk:
            instance.save(update_fields=[self.field.name,])

        if self.parent_role:
            # Add all non-null parent roles as parents
            paths = self.parent_role if type(self.parent_role) is list else [self.parent_role]
            for path in paths:
                if path.startswith("singleton:"):
                    parents = [Role.singleton(path[10:])]
                else:
                    parents = resolve_role_field(instance, path)
                for parent in parents:
                    role.parents.add(parent)

        if self.permissions is not None:
            permissions = RolePermission(
                role=role,
                resource=instance
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

    def __init__(self, role_name=None, role_description=None, permissions=None, parent_role=None, *args, **kwargs):
        self.role_name = role_name
        self.role_description = role_description
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
                    self.role_description,
                    self.permissions,
                    self.parent_role,
                    self
                )
                )
        post_init.connect(self._post_init, cls, True)
        post_save.connect(self._post_save, cls, True)
        post_delete.connect(self._post_delete, cls, True)
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


    def _post_init(self, instance, *args, **kwargs):
        if not self.parent_role:
            return

        if not instance.pk:
            return

        self._calc_original_parents(instance)

    def _calc_original_parents(self, instance):
        if not hasattr(self, '__original_parent_roles'):
            setattr(self, '__original_parent_roles', []) # do not just self.__original_parent_roles=[], it's not the same here
            paths = self.parent_role if type(self.parent_role) is list else [self.parent_role]
            original_parent_roles = set()
            for path in paths:
                if path.startswith("singleton:"):
                    parents = [Role.singleton(path[10:])]
                else:
                    parents = resolve_role_field(instance, path)
                for parent in parents:
                    original_parent_roles.add(parent)
            setattr(self, '__original_parent_roles', original_parent_roles)

    def _post_save(self, instance, created, *args, **kwargs):
        # Ensure that our field gets initialized after our first save
        this_role = getattr(instance, self.name)

        # As object relations change, the role hierarchy might also change if the relations
        # that changed were referenced in our magic parent_role field. This code synchronizes
        # these changes.
        if not self.parent_role:
            return

        if created:
            self._calc_original_parents(instance)
            return

        paths = self.parent_role if type(self.parent_role) is list else [self.parent_role]
        original_parents = getattr(self, '__original_parent_roles')
        new_parents = set()
        for path in paths:
            if path.startswith("singleton:"):
                parents = [Role.singleton(path[10:])]
            else:
                parents = resolve_role_field(instance, path)
            for parent in parents:
                new_parents.add(parent)

        Role.pause_role_ancestor_rebuilding()
        for role in original_parents - new_parents:
            this_role.parents.remove(role)
        for role in new_parents - original_parents:
            this_role.parents.add(role)
        Role.unpause_role_ancestor_rebuilding()

        setattr(self, '__original_parent_roles', new_parents)

    def _post_delete(self, instance, *args, **kwargs):
        this_role = getattr(instance, self.name)
        children = [c for c in this_role.children.all()]
        this_role.delete()
        for child in children:
            children.rebuild_role_ancestor_list()
