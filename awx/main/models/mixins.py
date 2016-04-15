# Django
from django.db import models
from django.db.models.aggregates import Max
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User # noqa

# AWX
from awx.main.models.rbac import (
    Role,
)


__all__ = ['ResourceMixin']

class ResourceMixin(models.Model):

    class Meta:
        abstract = True

    @classmethod
    def accessible_objects(cls, accessor, role_name):
        '''
        Use instead of `MyModel.objects` when you want to only consider
        resources that a user has specific permissions for. For example:

        MyModel.accessible_objects(user, {'read': True}).filter(name__istartswith='bar');

        NOTE: This should only be used for list type things. If you have a
        specific resource you want to check permissions on, it is more
        performant to resolve the resource in question then call
        `myresource.get_permissions(user)`.
        '''
        return ResourceMixin._accessible_objects(cls, accessor, role_name)

    @staticmethod
    def _accessible_objects(cls, accessor, role_name):
        if type(accessor) == User:
            kwargs = {}
            kwargs[role_name + '__ancestors__members'] = accessor
            qs = cls.objects.filter(**kwargs)
        elif type(accessor) == Role:
            kwargs = {}
            kwargs[role_name + '__ancestors'] = accessor
            qs = cls.objects.filter(**kwargs)
        else:
            accessor_type = ContentType.objects.get_for_model(accessor)
            roles = Role.objects.filter(content_type__pk=accessor_type.id,
                                        object_id=accessor.id)
            kwargs = {}
            kwargs[role_name + '__ancestors__in'] = roles
            qs = cls.objects.filter(**kwargs)

        #return cls.objects.filter(resource__in=qs)
        return qs


    def get_permissions(self, user):
        '''
        Returns a dict (or None) of the permissions a user has for a given
        resource.

        Note: Each field in the dict is the `or` of all respective permissions
        that have been granted to the roles that are applicable for the given
        user.

        In example, if a user has been granted read access through a permission
        on one role and write access through a permission on a separate role,
        the returned dict will denote that the user has both read and write
        access.
        '''

        return get_user_permissions_on_resource(self, user)


    def get_role_permissions(self, role):
        '''
        Returns a dict (or None) of the permissions a role has for a given
        resource.

        Note: Each field in the dict is the `or` of all respective permissions
        that have been granted to either the role or any descendents of that role.
        '''

        return get_role_permissions_on_resource(self, role)


    def accessible_by(self, user, permissions):
        '''
        Returns true if the user has all of the specified permissions
        '''

        perms = self.get_permissions(user)
        if perms is None:
            return False
        for k in permissions:
            if k not in perms or perms[k] < permissions[k]:
                return False
        return True
