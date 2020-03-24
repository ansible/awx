Starting from API V2, the Named URL feature lets users access Tower resources via resource-specific human-readable identifiers. Previously, the only way of accessing a resource object without auxiliary query string was via resource primary key number(*e.g.*, via URL path `/api/v2/hosts/2/`). Now users can use named URL to do the same thing, for example, via URL path `/api/v2/hosts/host_name++inv_name++org_name/`.


## Usage

There are two named-URL-related Tower configuration settings available under `/api/v2/settings/named-url/`: `NAMED_URL_FORMATS` and `NAMED_URL_GRAPH_NODES`.

`NAMED_URL_FORMATS` is a *read only* key-value pair list of all available named URL identifier formats. A typical `NAMED_URL_FORMATS` looks like this:
```
"NAMED_URL_FORMATS": {
    "job_templates": "<name>++<organization.name>",
    "workflow_job_templates": "<name>++<organization.name>",
    "workflow_job_template_nodes": "<identifier>++<workflow_job_template.name>++<organization.name>",
    "inventories": "<name>++<organization.name>",
    "users": "<username>",
    "applications": "<name>++<organization.name>",
    "inventory_scripts": "<name>++<organization.name>",
    "labels": "<name>++<organization.name>",
    "credential_types": "<name>+<kind>",
    "notification_templates": "<name>++<organization.name>",
    "instances": "<hostname>",
    "instance_groups": "<name>",
    "hosts": "<name>++<inventory.name>++<organization.name>",
    "groups": "<name>++<inventory.name>++<organization.name>",
    "organizations": "<name>",
    "credentials": "<name>++<credential_type.name>+<credential_type.kind>++<organization.name>",
    "teams": "<name>++<organization.name>",
    "inventory_sources": "<name>++<inventory.name>++<organization.name>",
    "projects": "<name>++<organization.name>"
},
```
For each item in `NAMED_URL_FORMATS`, the key is the API name of the resource to have named URL, the value is a string indicating how to form a human-readable unique identifiers for that resource. A typical procedure of composing named URL for a specific resource object using `NAMED_URL_FORMATS` is given below:

Suppose that a user wants to manually determine the named URL for a label with `id` `5`. She should first look up `labels` field of `NAMED_URL_FORMATS` and get the identifier format `<name>++<organization.name>`. The first part of the URL format is `<name>`, which indicates that she should get the label resource detail, `/api/v2/labels/5/`, and look for the `name` field in returned JSON.

Suppose the user has `name` field with value `'Foo'`; then the first part of our unique identifier is `Foo`. The second part of the format are double pluses `++`. That is the delimiter that separates different parts of a unique identifier, so simply append them to the unique identifier to get `Foo++`.

The third part of the format is `<organization.name>`, which indicates that field is not in the current label object under investigation, but in an organization which the label object points to. Thus, as the format indicates, the user should look up `organization` in `related` field of current returned JSON. That field may or may not exist; if it exists, follow the URL given in that field, say `/api/v2/organizations/3/`, to get the detail of the specific organization, extract its `name` field (*e.g.*, `'Default'`), and append it to our current unique identifier. Since `<organizations.name>` is the last part of format, we end up generating unique identifier for underlying label and have our named URL ready: `/api/v2/labels/Foo++Default/`.

In the case where `organization` does not exist in the `related` field of label object detail, we append empty string `''` instead, which essentially does not alter the current identifier. So `Foo++` becomes final unique identifier and thus generate named URL to be `/api/v2/labels/Foo++/`.

An important aspect of generating unique identifiers for named URL is dealing with reserved characters. Because the identifier is part of a URL, the following reserved characters by URL standard should be escaped to its percentage encoding: `;/?:@=&[]`. For example, if an organization is named `;/?:@=&[]`, its unique identifier should be `%3B%2F%3F%3A%40%3D%26%5B%5D`. Another special reserved character is `+`, which is not reserved by URL standard but used by named URL to link different parts of an identifier. It is escaped by `[+]`. For example, if an organization is named `[+]`, tis unique identifier is `%5B[+]%5D`, where original `[` and `]` are percent encoded and `+` is converted to `[+]`.

`NAMED_URL_FORMATS` exclusively lists every resource that can have named URL; any resource not listed there has no named URL. `NAMED_URL_FORMATS` alone should be instructive enough for users to compose human-readable unique identifier and named URL themselves. For more convenience, every object of a resource that can have named URL will have a related field `named_url` that displays that object's named URL. Users can simply copy-paste that field for their custom usages. Also, users are expected to see indications in the help text of the API browser if a resource object has named URL.

Although `NAMED_URL_FORMATS` is immutable on the user side, it will be automatically modified and expanded over time, reflecting underlying resource modification and expansion. Please consult `NAMED_URL_FORMATS` on the same Tower cluster where you want to use the named URL feature against.

`NAMED_URL_GRAPH_NODES` is another *read-only* list of key-value pairs that exposes the internal graph data structure that Tower uses to manage named URLs. This is not supposed to be human-readable but should be used for programmatically generating named URLs. An example script of generating a named URL given the primary key of arbitrary resource objects that can have named URL (using info provided by `NAMED_URL_GRAPH_NODES`) can be found as `/tools/scripts/pk_to_named_url.py`.


## Identifier Format Protocol

Resources in Tower are identifiable by their unique keys, which are basically tuples of resource fields. Every Tower resource is guaranteed to have its primary key number alone as a unique key, but there might be multiple other unique keys.

A resource can generate identifier formats and thus have named URL if it contains at least one unique key that satisfies rules below:

1. The key *contains and only contains* fields that are either the `name` field, or text fields with a finite number of possible choices (like credential type resource's `kind` field).
2. The only allowed exceptional fields that breaks the first rule is a many-to-one related field relating to a resource *other than self* which is also allowed to have a slug.

Here is an example for understanding the rules: Suppose Tower has resources `Foo` and `Bar`; both `Foo` and `Bar` contain a `name` field and a `choice` field that can only have value `'yes'` or `'no'`. Additionally, resource `Foo` contains a many-to-one field (a foreign key) relating to `Bar`, say `fk`. `Foo` has a unique key tuple `(name, choice, fk)` and `Bar` has a unique key tuple `(name, choice)`. Apparently `Bar` can have named URL because it satisfies rule 1. On the other hand, `Foo` can also have named URL, because although `Foo` breaks rule 1, the extra field breaking rule 1 is a `fk` field, which is many-to-one-related to `Bar` and `Bar` can have named URL.

For resources satisfying rule 1 above, their human-readable unique identifiers are combinations of foreign key fields, delimited by `+`. Specifically, resource `Bar` above will have the slug format `<name>+<choice>`. Note the field order matters in slug format: `name` field always comes first if present, followed by all the rest of the fields arranged in lexicographic order of field name. For example, if `Bar` also has an `a_choice` field satisfying rule 1 and the unique key becomes `(name, choice, a_choice)`, its slug format becomes `<name>+<a_choice>+<choice>`.

For resources satisfying rule 2 above instead, if we trace back via the extra foreign key fields, we end up getting a tree of resources that altogether identify objects of that resource. In order to generate identifier format, each resource in the traceback tree generates its own part of standalone format in the way described in the last paragraph, using all fields but the foreign keys. Finally all parts are combined by `++` in the following order:

* Put standalone format as the first identifier component.
* Recursively generate unique identifiers for each resource the underlying resource is pointing to by using a foreign key (a child of a traceback tree node).
* Treat generated unique identifiers as the rest identifier components. Sort them in lexicographic order of corresponding foreign key.
* Combine all components together using `++` to generate the final identifier format.

Back to the example above, when generating identifier format for resource `Foo`, we firstly generate standalone formats, `<name>+<choice>` for `Foo` and `<fk.name>+<fk.choice>` for `Bar`, then combine them together to be `<name>+<choice>++<fk.name>+<fk.choice>`.

When generating identifiers according to the given identifier format, there are cases where a foreign key might point nowhere. In this case, we substitute the part of the format corresponding to the resource the foreign key should point to with an empty string `''`. For example, if a `Foo` object has `name` to be `'alice'`, `choice` to be `'yes'`, but `fk` field `None`, its identifier will look like `alice+yes++`.


## Implementation Overview

Module `awx.main.utils.named_url_graph` stands at the core of named URL implementation. It exposes a single public function, `generate_graph`. `generate_graph` accepts a list of Tower models in Tower that might have named URL (meaning they have corresponding endpoints under `/api/v2/`), filter out those that are unable to have named URLs, and connect the rest together into a named URL graph. The graph is available as a settings option, `NAMED_URL_GRAPH`, and each node of it contains all info needed to generate named URL identifier formats and parse incoming named URL identifiers.

`generate_graph` will run only once for each Tower WSGI process. This is guaranteed by putting the function call inside `__init__` of `URLModificationMiddleware`. When an incoming request enters `URLModificationMiddleware`, the part of its URL path that could contain a valid named URL identifier is extracted and processed to find (possible) corresponding resource objects. The internal process is basically crawling against part of the named URL graph. If the object is found, the identifier part of the URL path is converted to the object's primary key. Going forward, Tower can treat the request with the old-styled URL.

## Job Template Organization Changes

The `organization` field was added as a read-only field to job templates, derived from its project organization.
This changed the named URL of job templates, to be compatible with multiple job templates with the same
name, but in different organizations.

To avoid making a backward-incompatible change, using the old named URL is still supported.
That means that you can still reference job templates by the `"job_templates": "<name>"` scheme.
If multiple job templates with the same name exist, the oldest one will be returned.

## Acceptance Criteria

In general, acceptance should follow what's in the "Usage" section. The contents in the "Identifier Format Protocol" section should not be relevant.

* The classical way of getting objects via primary keys should behave the same.
* Tower configuration for named URL should work as described. Particularly, `NAMED_URL_FORMATS` should be immutable on the user's side and display accurately-named URL identifier format info.
* `NAMED_URL_FORMATS` should be exclusive, meaning resources specified in `NAMED_URL_FORMATS` should have named URL, and resources not specified there should *not* have named URL.
* If a resource can have named URL, its objects should have a `named_url` field which represents the object-specific named URL. That field should only be visible under detail view, not list view.
* A user following the rules specified in `NAMED_URL_FORMATS` should be able to generate named URL exactly the same as the `named_url` field.
* A user should be able to access specified resource objects via an accurately-generated named URL. This includes not only the object itself but also its related URLs; for example, if `/api/v2/res_name/obj_slug/` is valid, then `/api/v2/res_name/obj_slug/related_res_name/` should also be valid.
* A user should not be able to access specified resource objects if the given named URL is inaccurate. For example, reserved characters not correctly escaped, or components whose corresponding foreign key field points nowhere but is not replaced by an empty string.
* A user should be able to dynamically generate named URLs by utilizing `NAMED_URL_GRAPH_NODES`.
