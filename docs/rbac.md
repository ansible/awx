# Role-Based Access Control (RBAC)

This document describes the RBAC implementation of the Ansible Tower Software.
The intended audience of this document is the Ansible Tower developer.

## Overview

### RBAC - System Basics

There are three main concepts to be familiar with: Roles, Resources, and Users.
Users can be members of a role, which gives them certain access to any
resources associated with that role, or any resources associated with "descendent"
roles.

For example, if I have an organization named "MyCompany" and I want to allow
two people, "Alice", and "Bob", access to manage all of the settings associated
with that organization, I'd make them both members of the organization's `admin_role`.

It is often the case that you have many Roles in a system, and you want some
roles to include all of the capabilities of other roles. For example, you may
want a System Administrator to have access to everything that an Organization
Administrator has access to, who has everything that a Project Administrator
has access to, and so on. We refer to this concept as the 'Role Hierarchy', and
is represented by allowing roles to have "Parent Roles". Any permission that a
role has is implicitly granted to any parent roles (or parents of those
parents, and so on). Of course roles can have more than one parent, and
capabilities are implicitly granted to all parents. (Technically speaking, this
forms a directional acyclic graph instead of a strict hierarchy, but the
concept should remain intuitive.)

![Example RBAC hierarchy](img/rbac_example.png?raw=true)


### Implementation Overview

The RBAC system allows you to create and layer roles for controlling access to resources. Any Django Model can
be made into a resource in the RBAC system by using the `ResourceMixin`. Once a model is accessible as a resource, you can
extend the model definition to have specific roles using the `ImplicitRoleField`. Within the declaration of
this role field you can also specify any parents the role may have, and the RBAC system will take care of
all of the appropriate ancestral binding that takes place behind the scenes to ensure that the model you've declared
is kept up to date as the relations in your model change.

### Roles

Roles are defined for a resource. If a role has any parents, these parents will be considered when determining
what roles are checked when accessing a resource.

    ResourceA
     |-- AdminRole

    ResourceB
     | -- AdminRole
           |-- parent = ResourceA.AdminRole

When a user attempts to access ResourceB, we will check for their access using the set of all unique roles, including the parents.

    ResourceA.AdminRole, ResourceB.AdminRole

This would provide any members of the above roles with access to ResourceB.

#### Singleton Role

There is a special case _Singleton Role_ that you can create. This type of role is for system-wide roles.

### Models

The RBAC system defines a few new models. These models represent the underlying RBAC implementation and generally will be abstracted away from your daily development tasks by the implicit fields and mixins.

#### `Role`

`Role` defines a single role within the RBAC implementation. It encapsulates the `ancestors`, `parents`, and `members` for a role. This model is intentionally kept dumb and it has no explicit knowledge of a `Resource`. The `Role` model (get it?), defines some methods that aid in the granting and creation of roles.

##### `visible_roles(cls, user)`

`visible_roles` is a class method that will look up all of the `Role` instances a user can "see". This includes any roles the user is a direct descendent of as well as any ancestor roles.

##### `singleton(cls, name)`

The `singleton` class method is a helper method on the `Role` model that helps in the creation of singleton roles. It will return the role by name if it already exists or create and return the new role in the case it does not.

##### `get_absolute_url(self)`

`get_absolute_url` returns the consumable URL endpoint for the `Role`.

##### `rebuild_role_ancestor_list(self)`

`rebuild_role_ancestor_list` will rebuild the current role ancestry that is stored in the `ancestors` field of a `Role`. This is called for you by `save` and different Django signals.

##### `is_ancestor_of(self, role)`

`is_ancestor_of` returns if the given `role` is an ancestor of the current `Role` instance.

##### `user in role`

You may use the `user in some_role` syntax to check and see if the specified
user is a member of the given role, **or** a member of any ancestor role.


### Fields

#### `ImplicitRoleField`

`ImplicitRoleField` fields are declared on your model. They provide the definition of grantable roles for accessing your resource. You may (and should) use the `parent_role` parameter to specify any parent roles that should inherit privileges implied by the role.

`parent_role` is the link to any parent roles you want considered when a user
is requesting access to your resource. A `parent_role` can be declared as a
single string, `"parent.read_role"`, or a list of many roles,
`['parentA.read_role', 'parentB.read_role']` which will make each listed role a parent. You can also use the syntax
`[('parentA.read_role', 'parentB.read_role'), 'parentC.read_role']` to make
`(parentA.read_role OR parentB.read_role) AND 'parentC.read_role` parents (so `parentB.read_role` will be added only if `parentA.read_role` was `None`).
If any listed role can't be evaluated (for example if there are `None` components in the path), then they are simply ignored until the value of the field changes.


### Mixins

#### `ResourceMixin`

By mixing in the `ResourceMixin` to your model, you are turning your model in to a resource in the eyes of the RBAC implementation. Your model will gain the helper methods that aid in the checking the access a users roles provides them to your resource.

##### `accessible_objects(cls, user, role_field)`

`accessible_objects` is a class method to use instead of `Model.objects`. This method will restrict the query of objects to only those that the user has access to - specifically those objects which the user is a member of the specified role (either directly or indirectly).

```python
    objects = MyModel.accessible_objects(user, 'admin_role')
    objects.filter(name__istartswith='december')
```

##### `get_permissions(self, user)`

`get_permissions` is an instance method that will give you the list of role names that the user has access to for a given object.

```python
    >>> instance.get_permissions(admin)
    ['admin_role', 'execute_role', 'read_role']
```

## Usage

After exploring the _Overview_, the usage of the RBAC implementation in your code should feel unobtrusive and natural.

```python
    # make your model a Resource
    class Document(Model, ResourceMixin):
       ...
    # declare your new role
    readonly_role = ImplicitRoleField(
        role_name="readonly",
        permissions={'read':True},
    )
```

Now that your model is a resource and has a `Role` defined, you can begin to access the helper methods provided to you by the `ResourceMixin` for checking a user's access to your resource. Here is the output of a Python REPL session:

```python
    # we've created some documents and a user
    >>> document = Document.objects.filter(pk=1)
    >>> user = User.objects.first()
    >>> user in document.read_role
    False  # not accessible by default
    >>> document.readonly_role.memebers.add(user)
    >>> user in document.read_role
    True   # now it is accessible
    >>> user in document.admin_role
    False  # my role does not have admin permission
```
