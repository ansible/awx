# Django
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User # noqa

# AWX
from awx.main.models.rbac import (
    Role, RoleAncestorEntry, get_roles_on_resource
)


__all__ = ['ResourceMixin']

class ResourceMixin(models.Model):

    class Meta:
        abstract = True

    @classmethod
    def accessible_objects(cls, accessor, role_field):
        '''
        Use instead of `MyModel.objects` when you want to only consider
        resources that a user has specific permissions for. For example:

        MyModel.accessible_objects(user, 'read_role').filter(name__istartswith='bar');

        NOTE: This should only be used for list type things. If you have a
        specific resource you want to check permissions on, it is more
        performant to resolve the resource in question then call
        `myresource.get_permissions(user)`.
        '''
        return ResourceMixin._accessible_objects(cls, accessor, role_field)

    @staticmethod
    def _accessible_objects(cls, accessor, role_field):
        if type(accessor) == User:
            ancestor_roles = accessor.roles.all()
        elif type(accessor) == Role:
            ancestor_roles = [accessor]
        else:
            accessor_type = ContentType.objects.get_for_model(accessor)
            ancestor_roles = Role.objects.filter(content_type__pk=accessor_type.id,
                                                 object_id=accessor.id)
        qs = cls.objects.filter(pk__in =
                                RoleAncestorEntry.objects.filter(
                                    ancestor__in=ancestor_roles,
                                    content_type_id = ContentType.objects.get_for_model(cls).id,
                                    role_field = role_field
                                ).values_list('object_id').distinct()
                                )
        return qs


    def get_permissions(self, accessor):
        '''
        Returns a dict (or None) of the roles a accessor has for a given resource.
        An accessor can be either a User, Role, or an arbitrary resource that
        contains one or more Roles associated with it.
        '''

        return get_roles_on_resource(self, accessor)

