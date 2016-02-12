# Django
from django.db import models
from django.db.models.aggregates import Max
from django.contrib.contenttypes.models import ContentType

# AWX
from awx.main.models.rbac import Resource
from awx.main.fields import ImplicitResourceField


__all__ = 'ResourceMixin'

class ResourceMixin(models.Model):

    class Meta:
        abstract = True

    resource = ImplicitResourceField()

    @classmethod
    def accessible_objects(cls, user, permissions):
        '''
        Use instead of `MyModel.objects` when you want to only consider
        resources that a user has specific permissions for. For example:

        MyModel.accessible_objects(user, {'read': True}).filter(name__istartswith='bar');

        NOTE: This should only be used for list type things. If you have a
        specific resource you want to check permissions on, it is more
        performant to resolve the resource in question then call
        `myresource.get_permissions(user)`.
        '''

        qs = Resource.objects.filter(
            content_type=ContentType.objects.get_for_model(cls),
            permissions__role__ancestors__members=user
        )
        for perm in permissions:
            qs = qs.annotate(**{'max_' + perm: Max('permissions__' + perm)})
            qs = qs.filter(**{'max_' + perm: int(permissions[perm])})

        return cls.objects.filter(resource__in=qs)


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

        qs = user.__class__.objects.filter(id=user.id, roles__descendents__permissions__resource=self.resource)

        qs = qs.annotate(max_create = Max('roles__descendents__permissions__create'))
        qs = qs.annotate(max_read = Max('roles__descendents__permissions__read'))
        qs = qs.annotate(max_write = Max('roles__descendents__permissions__write'))
        qs = qs.annotate(max_update = Max('roles__descendents__permissions__update'))
        qs = qs.annotate(max_delete = Max('roles__descendents__permissions__delete'))
        qs = qs.annotate(max_scm_update = Max('roles__descendents__permissions__scm_update'))
        qs = qs.annotate(max_execute = Max('roles__descendents__permissions__execute'))
        qs = qs.annotate(max_use = Max('roles__descendents__permissions__use'))

        qs = qs.values('max_create', 'max_read', 'max_write', 'max_update',
                       'max_delete', 'max_scm_update', 'max_execute', 'max_use')

        res = qs.all()
        if len(res):
            # strip away the 'max_' prefix
            return {k[4:]:v for k,v in res[0].items()}
        return None


    def accessible_by(self, user, permissions):
        '''
        Returns true if the user has all of the specified permissions
        '''

        perms = self.get_permissions(user)
        if not perms:
            return False
        for k in permissions:
            if k not in perms or perms[k] < permissions[k]:
                return False
        return True
