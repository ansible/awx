# Django
from django.db import models
from django.db import connection

# AWX
from awx.main.models.rbac import RolePermission, Role, RoleHierarchy
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
                                 ON (%(rbac_role_hierachy)s.ancestor_id = %(rbac_role)s_members.role_id)
                            LEFT JOIN %(rbac_permission)s 
                                 ON (%(rbac_permission)s.role_id = %(rbac_role_hierachy)s.role_id)
                           WHERE %(rbac_role)s_members.user_id=%(user_id)d
                                 %(where_clause)s
                           %(group_clause)s
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
                    'rbac_role_hierachy'     : RoleHierarchy._meta.db_table
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
                      LEFT JOIN %(rbac_role_hierachy)s 
                           ON (%(rbac_permission)s.role_id = %(rbac_role_hierachy)s.role_id)
                      LEFT JOIN %(rbac_role)s_members 
                           ON (
                                 %(rbac_role)s_members.role_id = %(rbac_role_hierachy)s.ancestor_id
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
                    'rbac_role_hierachy': RoleHierarchy._meta.db_table
                }
            )
            row = cursor.fetchone()
            if row:
                return dict(zip([x.name for x in cursor.description], row))
        return None

    def accessible_by(self, user, permissions):
        '''
        Returns true if the user has all of the specified permissions
        '''

        perms = self.get_permissions(user)
        for k in permissions:
            if k not in perms or perms[k] < permissions[k]:
                return False
        return True
