******************
Filtering
******************

.. index::
   single: filtering
   single: queryset

Any collection is what the system calls a "queryset" and can be filtered via various operators.

For example, to find the groups that contain the name "foo":

::

    http://<awx server name>/api/v2/groups/?name__contains=foo

To find an exact match:

::

    http://<awx server name>/api/v2/groups/?name=foo

If a resource is of an integer type, you must add ``\_\_int`` to the end to cast your string input value to an integer, like so:

::

    http://<awx server name>/api/v2/arbitrary_resource/?x__int=5

Related resources can also be queried, like so:

::

    http://<awx server name>/api/v2/users/?first_name__icontains=kim

This will return all users with names that include the string "Kim" in them.

You can also filter against multiple fields at once:

::

    http://<awx server name>/api/v2/groups/?name__icontains=test&has_active_failures=false

This finds all groups containing the name "test" that has no active failures.

For more about what types of operators are available, refer to: https://docs.djangoproject.com/en/dev/ref/models/querysets/


.. note::

    You can also watch the API as the UI is being used to see how it is filtering on various criteria.  




Any additional query string parameters may be used to filter the list of results returned to those matching a given value. Only fields and relations that exist in the database may be used for filtering. Any special characters in the specified value should be url-encoded. For example:

::

    ?field=value%20xyz

Fields may also span relations, only for fields and relationships defined in the database:

::

    ?other__field=value

To exclude results matching certain criteria, prefix the field parameter with ``not__``:

::

    ?not__field=value

By default, all query string filters are AND'ed together, so only the results matching all filters will be returned. To combine results matching any one of multiple criteria, prefix each query string parameter with ``or__``:

::

    ?or__field=value&or__field=othervalue
    ?or__not__field=value&or__field=othervalue

The default AND filtering applies all filters simultaneously to each related object being filtered across database relationships. The chain filter instead applies filters separately for each related object. To use, prefix the query string parameter with ``chain__``:

::

    ?chain__related__field=value&chain__related__field2=othervalue
    ?chain__not__related__field=value&chain__related__field2=othervalue

If the first query above were written as ``?related__field=value&related__field2=othervalue``, it would return only the primary objects where the same related object satisfied both conditions. As written using the chain filter, it would return the intersection of primary objects matching each condition.

Field lookups may also be used for more advanced queries, by appending the lookup to the field name:

::

    ?field__lookup=value

The following field lookups are supported:

- ``exact``: Exact match (default lookup if not specified).
- ``iexact``: Case-insensitive version of exact.
- ``contains``: Field contains value.
- ``icontains``: Case-insensitive version of contains.
- ``startswith``: Field starts with value.
- ``istartswith``: Case-insensitive version of startswith.
- ``endswith``: Field ends with value.
- ``iendswith``: Case-insensitive version of endswith.
- ``regex``: Field matches the given regular expression.
- ``iregex``: Case-insensitive version of regex.
- ``gt``: Greater than comparison.
- ``gte``: Greater than or equal to comparison.
- ``lt``: Less than comparison.
- ``lte``: Less than or equal to comparison.
- ``isnull``: Check whether the given field or related object is null; expects a boolean value.
- ``in``: Check whether the given field's value is present in the list provided; expects a list of items.
- Boolean values may be specified as ``True`` or ``1`` for true, ``False`` or ``0`` for false (both case-insensitive).

For example, ``?created__gte=2023-01-01`` will provide a list of items created after 1/1/2023.

Null values may be specified as ``None`` or ``Null`` (both case-insensitive), though it is preferred to use the ``isnull`` lookup to explicitly check for null values.

Lists (for the ``in`` lookup) may be specified as a comma-separated list of values.

Filtering based on the requesting user's level of access by query string parameter:

- ``role_level``: Level of role to filter on, such as ``admin_role``

