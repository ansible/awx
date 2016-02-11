# Django
from django.db import models
from django.db import connection
from django.db.models.aggregates import Max
from django.contrib.contenttypes.models import ContentType

# AWX
from awx.main.models.rbac import RolePermission, Role, Resource
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

        # TODO: Clean this up once we have settled on an optimal implementation

        if False:
            # This query does not work, but it is not apparent to me at this
            # time why it does not. The intent is to be able to return a query
            # set that does not involve a subselect, with the hope that this
            # will perform better than our subselect method. I'm leaving it
            # here for now so that I can revisit it with fresh eyes and
            # hopefully find the issue.
            #
            # If someone else comes along and fixes or eliminates this, please
            # tag me or let me know! - anoek 2016-02-11

            qs = cls.objects
            for perm in permissions:
                kw = {'max_' + perm: Max('resource__permissions__' + perm)}
                qs = qs.annotate(**kw)
                kw = {'max_' + perm: int(permissions[perm])}
                qs = qs.filter(**kw)
            qs = qs.filter(resource__permissions__role__ancestors__members=user)
            return qs

        if True:
            # Begin working code.. this results in a subselect which I'm not too
            # thrilled about, but performs reasonably ok

            qs = Resource.objects.filter(
                content_type=ContentType.objects.get_for_model(cls),
                permissions__role__ancestors__members=user
            )
            for perm in permissions:
                kw = {'max_' + perm: Max('permissions__' + perm)}
                qs = qs.annotate(**kw)
                kw = {'max_' + perm: int(permissions[perm])}
                qs = qs.filter(**kw)

            return cls.objects.filter(resource__in=qs)

        if False:
            # This works and remains the most performant implementation. Keeping it here
            # until we can dethrone it with a proper ORM implementation

            aggregate_where_clause = ''
            aggregates = ''
            group_clause = ''
            where_clause = ''

            if len(permissions) > 1:
                group_clause = 'GROUP BY %s.resource_id' % RolePermission._meta.db_table
                for perm in permissions:
                    if not aggregate_where_clause:
                        aggregate_where_clause = 'WHERE '
                    else:
                        aggregate_where_clause += ' AND '
                    aggregate_where_clause += '"%s" = %d' % (perm, int(permissions[perm]))
                    aggregates += ', MAX("%s") as "%s"' % (perm, perm)
            if len(permissions) == 1:
                perm = list(permissions.keys())[0]
                where_clause = 'AND "%s" = %d' % (perm, int(permissions[perm]))

            return cls.objects.extra(
                where=[
                    '''
                        %(table_name)s.resource_id in (
                          SELECT resource_id FROM (
                              SELECT %(rbac_permission)s.resource_id %(aggregates)s
                                FROM %(rbac_role)s_members
                                LEFT JOIN %(rbac_role_hierachy)s
                                     ON (%(rbac_role_hierachy)s.to_role_id = %(rbac_role)s_members.role_id)
                                LEFT JOIN %(rbac_permission)s
                                     ON (%(rbac_permission)s.role_id = %(rbac_role_hierachy)s.from_role_id)
                               WHERE %(rbac_role)s_members.user_id=%(user_id)d
                                     %(where_clause)s
                               %(group_clause)s
                               order by resource_id
                          ) summarized_permissions
                          %(aggregate_where_clause)s
                        )
                    '''
                    %
                    {
                        'table_name'             : cls._meta.db_table,
                        'aggregates'             : aggregates,
                        'user_id'                : user.id,
                        'aggregate_where_clause' : aggregate_where_clause,
                        'group_clause'           : group_clause,
                        'where_clause'           : where_clause,
                        'rbac_role'              : Role._meta.db_table,
                        'rbac_permission'        : RolePermission._meta.db_table,
                        'rbac_role_hierachy'     : 'main_rbac_roles_ancestors'
                    }
                ]
            )


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

        # TODO: Clean this up once we have settled on an optimal implementation

        if True:
            # This works well enough at scale, but is about 5x slower than the
            # raw sql variant, further optimization is desired.

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

            #print('###############')
            #print(qs.query)
            #print('###############')

            res = qs.all()
            if len(res):
                return {k[4:]:v for k,v in res[0].items()}
            return None


        if False:
            # This works and remains the most performant implementation. Keeping it here
            # until we can dethrone it with a proper ORM implementation

            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                        SELECT
                              MAX("create")     as "create",
                              MAX("read")       as "read",
                              MAX("write")      as "write",
                              MAX("update")     as "update",
                              MAX("delete")     as "delete",
                              MAX("scm_update") as "scm_update",
                              MAX("execute")    as "execute",
                              MAX("use")        as "use"

                          FROM %(rbac_permission)s
                          LEFT JOIN main_rbac_roles_ancestors
                               ON (%(rbac_permission)s.role_id = main_rbac_roles_ancestors.from_role_id)
                         INNER JOIN %(rbac_role)s_members
                               ON (
                                     %(rbac_role)s_members.role_id = main_rbac_roles_ancestors.to_role_id
                                     AND %(rbac_role)s_members.user_id = %(user_id)d
                                  )

                         WHERE %(rbac_permission)s.resource_id=%(resource_id)s
                         GROUP BY %(rbac_role)s_members.user_id
                    '''
                    %
                    {
                        'user_id': user.id,
                        'resource_id': self.resource.id,
                        'rbac_role': Role._meta.db_table,
                        'rbac_permission': RolePermission._meta.db_table,
                        #'rbac_role_hierachy': RoleHierarchy._meta.db_table
                    }
                )
                row = cursor.fetchone()
                if row:
                    return dict(zip([x[0] for x in cursor.description], row))
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
