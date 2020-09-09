factories
=========

This is a module for defining stand-alone factories and fixtures. Ideally a fixture will implement a single item.
DO NOT decorate fixtures in this module with the @pytest.fixture. These fixtures are to be combined
with fixture factories and composition using the `conftest.py` convention. Those composed fixtures
will be decorated for usage and discovery.

Use the fixtures directly in factory methods to build up the desired set of components and relationships.
Each fixture should create exactly one object and should support the option for that object to be persisted
or not.

A factory should create at a minimum a single object for that factory type. The creation of any
associated objects should be explicit. For example, the `create_organization` factory when given only
a `name` parameter will create an Organization but it will not implicitly create any other objects.

teams
-----

There is some special handling for users when adding teams. There is a short hand that allows you to
assign a user to the member\_role of a team using the string notation of `team_name:user_name`. There is
no shortcut for adding a user to the admin\_role of a team. See the roles section for more information
about how to do that.

roles
-----

The roles helper allows you pass in roles to a factory. These roles assignments will happen after
the objects are created. Using the roles parameter required that persisted=True (default).

You can use a string notation of `object_name.role_name:user` OR `object_name.role_name:object_name.child_role`

    obj.parent_role:user  # This will make the user a member of parent_role
    obj1.role:obj2.role   # This will make obj2 a child role of obj1

    team1.admin_role:joe
    team1.admin_role:project1.admin_role

examples
--------

    objects = create_organization('test-org')
    assert objects.organization.name == 'test-org'

    objects = create_organization('test-org', projects=['test-proj'])
    assert objects.projects.test-proj.organization == objects.organization

    objects = create_organization('test-org', persisted=False)
    assert not objects.organization.pk

patterns
--------

`mk` functions are single object fixtures. They should create only a single object with the minimum deps.
They should also accept a `persisted` flag, if they must be persisted to work, they raise an error if persisted=False

`generate` and `apply` functions are helpers that build up the various parts of a `create` functions objects. These
should be useful for more than one create function to use and should explicitly accept all of the values needed
to execute. These functions should also be robust and have very specific error reporting about constraints and/or
bad values.

`create` functions compose many of the `mk` and `generate` functions to make different object
factories. These functions when giving the minimum set of arguments should only produce a
single artifact (or the minimum needed for that object). These should be wrapped by discoverable
fixtures in various conftest.py files.
