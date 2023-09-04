******************
Access Resources
******************

.. index::
   single: access resources

Traditionally, AWX uses a primary key to access individual resource objects. The named URL feature allows you to access AWX resources via resource-specific human-readable identifiers. The named URL via URL path ``/api/v2/hosts/host_name++inv_name++org_name/``, for example, allows you to access a resource object without an auxiliary query string.

Configuration Settings
=========================

There are two named-URL-related configuration settings available under ``/api/v2/settings/named-url/``: ``NAMED_URL_FORMATS`` and ``NAMED_URL_GRAPH_NODES``.

``NAMED_URL_FORMATS`` is a read only key-value pair list of all available named URL identifier formats. A typical ``NAMED_URL_FORMATS`` looks like this:

::

	"NAMED_URL_FORMATS": {
    	"organizations": "<name>",
        "teams": "<name>++<organization.name>",
        "credential_types": "<name>+<kind>",
        "credentials": "<name>++<credential_type.name>+<credential_type.kind>++<organization.name>",
        "notification_templates": "<name>++<organization.name>",
        "job_templates": "<name>++<organization.name>",
        "projects": "<name>++<organization.name>",
        "inventories": "<name>++<organization.name>",
        "hosts": "<name>++<inventory.name>++<organization.name>",
        "groups": "<name>++<inventory.name>++<organization.name>",
        "inventory_sources": "<name>++<inventory.name>++<organization.name>",
        "inventory_scripts": "<name>++<organization.name>",
        "instance_groups": "<name>",
        "labels": "<name>++<organization.name>",
        "workflow_job_templates": "<name>++<organization.name>",
        "workflow_job_template_nodes": "<identifier>++<workflow_job_template.name>++<organization.name>",
        "applications": "<name>++<organization.name>",
        "users": "<username>",
        "instances": "<hostname>"
	}

For each item in ``NAMED_URL_FORMATS``, the key is the API name of the resource to have named URL, the value is a string indicating how to form a human-readable unique identifier for that resource. ``NAMED_URL_FORMATS`` exclusively lists every resource that can have named URL, any resource not listed there has no named URL. If a resource can have named URL, its objects should have a named_url field which represents the object-specific named URL. That field should only be visible under detail view, not list view. You can access specified resource objects using accurately generated named URL. This includes not only the object itself but also its related URLs. For example, if ``/api/v2/res_name/obj_slug/`` is valid, ``/api/v2/res_name/obj_slug/related_res_name/`` should also be valid.

``NAMED_URL_FORMATS`` are instructive enough to compose human-readable unique identifier and named URL themselves. For ease-of-use, every object of a resource that can have named URL will have a related field ``named_url`` that displays that object's named URL. You can copy and paste that field for your own custom use. Also refer to the help text of API browser if a resource object has named URL for further guidance.

Suppose you want to manually determine the named URL for a label with ID 5. A typical procedure of composing a named URL for this specific resource object using ``NAMED_URL_FORMATS`` is to first look up the labels field of ``NAMED_URL_FORMATS`` to get the identifier format ``<name>++<organization.name>``:

	- The first part of the URL format is ``<name>``, which indicates that the label resource detail can be found in ``/api/v2/labels/5/``, and look for ``name`` field in returned JSON. Suppose you have the ``name`` field with value 'Foo', then the first part of the unique identifier is **Foo**. 
	- The second part of the format are double pluses ++. That is the delimiter that separates different parts of a unique identifier. Append them to the unique identifier to get **Foo++** 
	- The third part of the format is ``<organization.name>``, which indicates that field is not in the current label object under investigation, but in an organization which the label object points to. Thus, as the format indicates, look up the organization in the related field of current returned JSON. That field may or may not exist. If it exists, follow the URL given in that field, for example, ``/api/v2/organizations/3/``, to get the detail of the specific organization, extract its ``name`` field, for example, 'Default', and append it to our current unique identifier. Since ``<organizations.name>`` is the last part of format, thus, generating the resulting named URL: ``/api/v2/labels/Foo++Default/``.  In the case where organization does not exist in related field of the label object detail, append an empty string instead, which essentially does not alter the current identifier. So ``Foo++`` becomes the final unique identifier and the resulting generated named URL becomes ``/api/v2/labels/Foo++/``.

An important aspect of generating a unique identifier for named URL has to do with reserved characters. Because the identifier is part of a URL, the following reserved characters by URL standard is encoded by percentage symbols: ``;/?:@=&[]``. For example, if an organization is named ``;/?:@=&[]``, its unique identifier should be ``%3B%2F%3F%3A%40%3D%26%5B%5D``. Another special reserved character is ``+``, which is not reserved by URL standard but used by named URL to link different parts of an identifier. It is encoded by ``[+]``. For example, if an organization is named ``[+]``, its unique identifier is ``%5B[+]%5D``, where original ``[`` and ``]`` are percent encoded and ``+`` is converted to ``[+]``.

Although ``NAMED_URL_FORMATS`` cannot be manually modified, modifications do occur automatically and expanded over time, reflecting underlying resource modification and expansion. Consult the ``NAMED_URL_FORMATS`` on the same cluster where you want to use the named URL feature.

``NAMED_URL_GRAPH_NODES`` is another read-only list of key-value pairs that exposes the internal graph data structure used to manage named URLs. This is not intended to be human-readable but should be used for programmatically generating named URLs. An example script for generating named URL given the primary key of arbitrary resource objects that can have a named URL, using info provided by ``NAMED_URL_GRAPH_NODES``, can be found in GitHub at https://github.com/ansible/awx/blob/devel/tools/scripts/pk_to_named_url.py.

Identifier Format Protocol
===============================

Resources are identifiable by their unique keys, which are basically tuples of resource fields. Every resource is guaranteed to have its primary key number alone as a unique key, but there might be multiple other unique keys. A resource can generate an identifier format thus, have a named URL if it contains at least one unique key that satisfies the rules below:

1. The key must contain only fields that are either the ``name`` field, or text fields with a finite number of possible choices (like credential type resource's ``kind`` field).

2. The only allowed exceptional fields that breaks rule #1 is a many-to-one related field relating to a resource other than itself, which is also allowed to have a slug.

Suppose there are resources ``Foo`` and ``Bar``, both ``Foo`` and ``Bar`` contain a ``name`` field and a ``choice`` field that can only have value 'yes' or 'no'. Additionally, resource ``Foo`` contains a many-to-one field (a foreign key) relating to ``Bar``, e.g. ``fk``. ``Foo`` has a unique key tuple (``name``, ``choice``, ``fk``) and ``Bar`` has a unique key tuple (``name``, ``choice``). ``Bar`` can have named URL because it satisfies rule #1 above. ``Foo`` can also have named URL, even though it breaks rule #1, the extra field breaking rule #1 is the ``fk`` field, which is many-to-one-related to ``Bar`` and ``Bar`` can have named URL.

For resources satisfying rule #1 above, their human-readable unique identifiers are combinations of foreign key fields, delimited by ``+``. In specific, resource ``Bar`` in the above example will have slug format ``<name>+<choice>``. Note the field order matters in slug format: ``name`` field always comes first if present, following by all the rest fields arranged in lexicographic order of field name. For example, if Bar also has an ``a_choice`` field satisfying rule #1 and the unique key becomes (``name``, ``choice``, ``a_choice``), its slug format becomes ``<name>+<a_choice>+<choice>``.

For resources satisfying rule #2 above, if traced back via the extra foreign key fields, the result is a tree of resources that all together identify objects of that resource. In order to generate identifier format, each resource in the traceback tree generates its own part of standalone format in the way previously described, using all fields but the foreign keys. Finally all parts are combined by ``++`` in the following order:

- Put stand-alone format as the first identifier component.
- Recursively generate unique identifiers for each resource. The underlying resource is pointing to using a foreign key (a child of a traceback tree node).
- Treat generated unique identifiers as the rest of the identifier components. Sort them in lexicographic order of corresponding foreign keys.
- Combine all components together using ``++`` to generate the final identifier format.

In reference to the example above, when generating an identifier format for resource ``Foo``, AWX generates the stand-alone formats, ``<name>+<choice>`` for ``Foo`` and ``<fk.name>+<fk.choice>`` for ``Bar``, then combine them together to be ``<name>+<choice>++<fk.name>+<fk.choice>``.

When generating identifiers according to the given identifier format, there are cases where a foreign key may point to nowhere. In this case, AWX substitutes the part of the format corresponding to the resource the foreign key should point to with an empty string ''. For example, if a ``Foo`` object has the name ='alice', choice ='yes', but ``fk`` field = None, its resulting identifier will be ``alice+yes++``.
