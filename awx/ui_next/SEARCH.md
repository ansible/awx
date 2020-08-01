# Simple Search

## UX Considerations

Historically, the code that powers search in the AngularJS version of the AWX/Tower UI is very complex and prone to bugs.  In order to reduce that complexity, we've made some UX decisions to help make the code easier to maintain.

**ALL query params namespaced and in url bar**

This includes lists that aren't necessarily hyperlinked, like lookup lists.  The reason behind this is so we can treat the url bar as the source of truth for queries always.  Any params that have both a key AND value that is in the defaultParams section of the qs config are stripped out of the search string (see "Encoding for UI vs. API" for more info on this point)

**Django fuzzy search (`?search=`) is not accessible outside of "advanced search"**

In current smart search typing a term with no key utilizes `?search=` i.e. for "foo" tag, `?search=foo` is given.  `?search=` looks on a static list of field name "guesses" (such as name, description, etc.), as well as specific fields as defined for each endpoint (for example, the events endpoint looks for a "stdout" field as well).  Due to the fact a key will always be present on the left-hand of simple search, it doesn't make sense to use `?search=` as the default.

We may allow passing of `?search=` through our future advanced search interface.  Some details that were gathered in planning phases about `?search=` that might be helpful in the future:
- `?search=` tags are OR'd together (union is returned).
- `?search=foo&name=bar` returns items that have a name field of bar (not case insensitive) AND some text field with foo on it
- `?search=foo&search=bar&name=baz` returns (foo in name OR foo in description OR ...) AND (bar in name OR bar in description OR ...) AND (baz in name)
- similarly `?related__search=` looks on the static list of "guesses" for models related to the endpoint.  The specific fields are not "searched" for `?related__search=`.
- `?related__search=` not currently used in awx ui

**A note on clicking a tag to putting it back into the search bar**

This was brought up as a nice to have when we were discussing our initial implementation of search in the new application.  Since there isn't a way we would be able to know if the user created the tag from the simple or advanced search interface, we wouldn't know where to put it back.  This breaks our idea of using the query params as the exclusive source of truth, so we've decided against implementing it for now.

## Tasklist

### DONE

- DONE update handleSearch to follow handleSort param
- DONE update qsConfig columns to utilize isSearchable bool (just like isSortable bool)
- DONE enter keydown in text search bar to search
- DONE get decoded params and write test
- DONE make list header component
- DONE make filter component
- DONE make filters show up for empty list
- DONE make clear all button
- DONE styling of FilterTags component
- DONE clear out text input after tag has been made
- DONE deal with duplicate key tags being added/removed in qs util file
- DONE deal with widgetry changing between one dropdown option to the left of search and many
- DONE bug: figure out why ?name=org returning just org not “org 2”
- DONE update contrib file to have the first section with updated text as is in this pr description.
- DONE rebase with latest awx-pf changes
- DONE styling of search bar
- DONE make filter and list header tests
- DONE change api paramsSerializer to handle duplicate key stuff
- DONE update qs update function to be smaller, simple param functions, as opposed to one big one with a lot of params
- DONE add search filter removal test for qs.
- DONE remove button for search tags of duplicate keys are broken, fix that

### TODO pre-holiday break
- Update COLUMNS to SORT_COLUMNS and SEARCH_COLUMNS
- Update to using new PF Toolbar component (currently an experimental component)
- Change the right-hand input based on the type of key selected on the left-hand side.  In addition to text input, for our MVP we will support:
  - number input
  - select input (multiple-choice configured from UI or Options)
- Update the following lists to have the following keys:

**Jobs list** (signed off earlier in chat)
  - Name (which is also the name of the job template) - search is ?name=jt
  - Job ID - search is ?id=13
  - Label name - search is ?labels__name=foo
  - Job type (dropdown on right with the different types) ?type = job
  - Created by (username) - search is ?created_by__username=admin
  - Status - search (dropdown on right with different statuses) is ?status=successful

Instances of jobs list include:
  - Jobs list
  - Host completed jobs list
  - JT completed jobs list

**Organization list**
  - Name - search is ?name=org
  - ? Team name (of a team in the org) - search is ?teams__name=ansible
  - ? Username (of a user in the org) - search is ?users__username=johndoe

Instances of orgs list include:
  - Orgs list
  - User orgs list
  - Lookup on Project
  - Lookup on Credential
  - Lookup on Inventory
  - User access add wizard list
  - Team access add wizard list

**Instance Groups list**
  - Name - search is ?name=ig
  - ? is_containerized boolean choice (doesn't work right now in API but will soon) - search is ?is_containerized=true
  - ? credential name - search is ?credentials__name=kubey

Instance of instance groups list include:
  - Lookup on Org
  - Lookup on JT
  - Lookup on Inventory

**Users list**
  - Username - search is ?username=johndoe
  - First Name - search is ?first_name=John
  - Last Name - search is ?last_name=Doe
  - ? (if not superfluous, would not include on Team users list) Team Name - search is ?teams__name=team_of_john_does (note API issue: User has no field named "teams")
  - ? (only for access or permissions list) Role Name - search is ?roles__name=Admin (note API issue: Role has no field "name")
  - ? (if not superfluous, would not include on Organization users list) ORg Name - search is ?organizations__name=org_of_jhn_does

Instance of user lists include:
  - User list
  - Org user list
  - Access list for Org, JT, Project, Credential, Inventory, User and Team
  - Access list for JT
  - Access list Project
  - Access list for Credential
  - Access list for Inventory
  - Access list for User
  - Access list for Team
  - Team add users list
  - Users list in access wizard (to add new roles for a particular list) for Org
  - Users list in access wizard (to add new roles for a particular list) for JT
  - Users list in access wizard (to add new roles for a particular list) for Project
  - Users list in access wizard (to add new roles for a particular list) for Credential
  - Users list in access wizard (to add new roles for a particular list) for Inventory

**Teams list**
  - Name - search is ?name=teamname
  - ? Username (of a user in the team) - search is ?users__username=johndoe
  - ? (if not superfluous, would not include on Organizations teams list) Org Name - search is ?organizations__name=org_of_john_does

Instance of team lists include:
  - Team list
  - Org team list
  - User team list
  - Team list in access wizard (to add new roles for a particular list) for Org
  - Team list in access wizard (to add new roles for a particular list) for JT
  - Team list in access wizard (to add new roles for a particular list) for Project
  - Team list in access wizard (to add new roles for a particular list) for Credential
  - Team list in access wizard (to add new roles for a particular list) for Inventory

**Credentials list**
  - Name
  - ? Type (dropdown on right with different types) 
  - ? Created by (username)
  - ? Modified by (username)

Instance of credential lists include:
  - Credential list
  - Lookup for JT
  - Lookup for Project
  - User access add wizard list
  - Team access add wizard list

**Projects list**
  - Name - search is ?name=proj
  - ? Type (dropdown on right with different types) - search is scm_type=git
  - ? SCM URL - search is ?scm_url=github.com/ansible/test-playbooks
  - ? Created by (username) - search is ?created_by__username=admin
  - ? Modified by (username) - search is ?modified_by__username=admin

Instance of project lists include:
  - Project list
  - Lookup for JT
  - User access add wizard list
  - Team access add wizard list

**Templates list**
  - Name - search is ?name=cleanup
  - ? Type (dropdown on right with different types) - search is ?type=playbook_run
  - ? Playbook name - search is ?job_template__playbook=debug.yml
  - ? Created by (username) - search is ?created_by__username=admin
  - ? Modified by (username) - search is ?modified_by__username=admin

Instance of template lists include:
  - Template list
  - Project Templates list

**Inventories list**
  - Name - search is ?name=inv
  - ? Created by (username) - search is ?created_by__username=admin
  - ? Modified by (username) - search is ?modified_by__username=admin

Instance of inventory lists include:
  - Inventory list
  - Lookup for JT
  - User access add wizard list
  - Team access add wizard list

**Groups list**
  - Name - search is ?name=group_name
  - ? Created by (username) - search is ?created_by__username=admin
  - ? Modified by (username) - search is ?modified_by__username=admin

Instance of group lists include:
  - Group list

**Hosts list**
  - Name - search is ?name=hostname
  - ? Created by (username) - search is ?created_by__username=admin
  - ? Modified by (username) - search is ?modified_by__username=admin

Instance of host lists include:
  - Host list

**Notifications list**
  - Name - search is ?name=notification_template_name
  - ? Type (dropdown on right with different types) - search is ?type=slack
  - ? Created by (username) - search is ?created_by__username=admin
  - ? Modified by (username) - search is ?modified_by__username=admin

Instance of notification lists include:
  - Org notification list
  - JT notification list
  - Project notification list

### TODO backlog
- Change the right-hand input based on the type of key selected on the left-hand side.  We will eventually want to support:
  - lookup input (selection of particular resources, based on API list endpoints)
  - date picker input
- Update the following lists to have the following keys:
  - Update all __name and __username related field search-based keys to be type-ahead lookup based searches

## Code Details

### Search component

The component looks like this:

```
<Search
  qsConfig={qsConfig}
  columns={columns}
  onSearch={onSearch}
/>
```

**qsConfig** is used to get namespace so that multiple lists can be on the page.  When tags are modified they append namespace to query params.  The qsConfig is also used to get "type" of fields in order to correctly parse values as int or date as it is translating.

**columns** are passed as an array, as defined in the screen where the list is located. You pass a bool `isDefault` to indicate that should be the key that shows up in the left-hand dropdown as default in the UI.  If you don't pass any columns, a default of `isDefault=true` will be added to a name column, which is nearly universally shared throughout the models of awx.

There is a type attribute that can be `'string'`, `'number'` or `'choice'` (and in the future, `'date'` and `'lookup'`), which will change the type of input on the right-hand side of the search bar.  For a key that has a set number of choices, you will pass a choices attribute, which is an array in the format choices: [{label: 'Foo', value: 'foo'}]

**onSearch** calls the `mergeParams` qs util in order to add new tags to the queryset.  mergeParams is used so that we can support duplicate keys (see mergeParams vs. replaceParams for more info).

### ListHeader component

`DataListToolbar`, `EmptyListControls`, and `FilterTags` components were created or moved to a new sub-component of `PaginatedDataList`, `ListHeader`. This allowed us to consolidate the logic between both lists with data (which need to show search, sort, any search tags currently active, and actions) as well as empty lists (which need to show search tags currently active so they can be removed, potentially getting you back to a "list-has-data" state, as well as a subset of options still valid, such as "add").

The ability to search and remove filters, as well as sort the list is handled through callbacks which are passed from functions defined in `ListHeader`. These are the following:

- `handleSort(key, direction)` - use key and direction of sort to change the order_by value in the queryset
- `handleSearch(key, value)` - use key and value to push a new value to the param
- `handleRemove(key, value)` - use key and value to remove a value to the param
- `handleRemoveAll()` - remove all non-default params

All of these functions act on the react-router history using the `pushHistoryState` function. This causes the query params in the url to update, which in turn triggers change handlers that will re-fetch data for the lists.

**a note on sort_columns and search_columns**

We have split out column configuration into separate search and sort column array props--these are passed to the search and sort columns.  Both accept an isDefault prop for one of the items in the array to be the default option selected when going to the page.  Sort column items can pass an isNumeric boolean in order to chnage the iconography of the sort UI element.  Search column items can pass type and if applicable choices, in order to configure the right-hand side of the search bar.

### FilterTags component

Similar to the way the list grabs data based on changes to the react-router params, the `FilterTags` component updates when new params are added. This component is a fairly straight-forward map (only slightly complex, because it needed to do a nested map over any values with duplicate keys that were represented by an inner-array).  Both key and value are displayed for the tag.

### qs utility

The qs (queryset) utility is used to make the search speak the language of the REST API.  The main functions of the utilities are to:
- add, replace and remove filters
- translate filters as url params (for linking and maintaining state), in-memory representation (as JS objects), and params that Django REST Framework understands.

More info in the below sections:

#### Encoding for UI vs. API

For the UI url params, we want to only encode those params that aren't defaults, as the default behavior was defined through configuration and we don't need these in the url as a source of truth.  For the API, we need to pass these params so that they are taken into account when the response is built.

#### mergeParams vs. replaceParams

**mergeParams** is used to suppport putting values with the same key 

From a UX perspective, we wanted to be able to support searching on the same key multiple times (i.e. searching for things like `?foo=bar&foo=baz`). We do this by creating an array of all values. i.e.:

```
{
  foo: ['bar', 'baz']
}
```

Concatenating terms in this way gives you the intersection of both terms (i.e. foo must be "bar" and "baz").  This is helpful for the most-common type of searching, substring (`__icontains`) searches.  This will increase filtering, allowing the user to drill-down into the list as terms are added.

**replaceParams** is used to support sorting, setting page_size, etc.  These params only allow one choice, and we need to replace a particular key's value if one is passed.

#### Working with REST API

The REST API is coupled with the qs util through the `paramsSerializer`, due to the fact we need axios to support the array for duplicate key values in the object representation of the params to pass to the get request.  This is done where axios is configured in the Base.js file, so all requests and request types should support our array syntax for duplicate keys automatically.

# Advanced Search - this section is a mess, update eventually

**a note on typing in a smart search query**

In order to not support a special "language" or "syntax" for crafting the query like we have now (and is the cause of a large amount of bugs), we will not support the old way of typing in a filter like in the current implementation of search.

Since all search bars are represented in the url, for users who want to input a string to filter results in a single step, typing directly in the url to achieve the filter is acceptable.

# Advanced search notes

Current thinking is Advanced Search will be post-3.6, or at least late 3.6 after awx features and "simple search" with the left dropdown and right input for the above phase 1 lists.

That being said, we want to plan it out so we make sure the infrastructure of how we set up adding/removing tags, what shows up in the url bar, etc. all doesn't have to be redone.

Users will get to advanced search with a button to the right of search bar.  When selected type-ahead key thing opens, left dropdown of search bar goes away, and x is given to get back to regular search (this is in the mockups)

It is okay to only make this typing representation available initially (i.e. they start doing stuff with the type-ahead and the phases, no more typing in to make a query that way).

when you click through or type in the search bar for the various phases of crafting the query ("not", "related resource project", "related resource key name", "value foo") which might be represented in the top bar as a series of tags that can be added and removed before submitting the tag.

We will try to form options data from a static file.  Because options data is static, we may be able to generate and store as a static file of some sort (that we can use for managing smart search).  Alan had ideas around this.  If we do this it will mean we don't have to make a ton of requests as we craft smart search filters.  It sounds like tower cli may start using something similar.

## Smart search flow

Smart search will be able to craft the tag through various states.  Note that the phases don't necessarily need to be completed in sequential order.

  PHASE 1: prefix operators

**TODO: Double check there's no reason we need to include or__ and chain__ and can just do not__**

  - not__
  - or__
  - chain__

  how these work:

  To exclude results matching certain criteria, prefix the field parameter with not__:

  ?not__field=value
  By default, all query string filters are AND'ed together, so only the results matching all filters will be returned. To combine results matching any one of multiple criteria, prefix each query string parameter with or__:

  ?or__field=value&or__field=othervalue
  ?or__not__field=value&or__field=othervalue
  (Added in Ansible Tower 1.4.5) The default AND filtering applies all filters simultaneously to each related object being filtered across database relationships. The chain filter instead applies filters separately for each related object. To use, prefix the query string parameter with chain__:

  ?chain__related__field=value&chain__related__field2=othervalue
  ?chain__not__related__field=value&chain__related__field2=othervalue
  If the first query above were written as ?related__field=value&related__field2=othervalue, it would return only the primary objects where the same related object satisfied both conditions. As written using the chain filter, it would return the intersection of primary objects matching each condition.

  PHASE 2: related fields, given by array, where __search is appended to them, i.e.

  ```
  "related_search_fields": [
        "credentials__search",
        "labels__search",
        "created_by__search",
        "modified_by__search",
        "notification_templates__search",
        "custom_inventory_scripts__search",
        "notification_templates_error__search",
        "notification_templates_success__search",
        "notification_templates_any__search",
        "teams__search",
        "projects__search",
        "inventories__search",
        "applications__search",
        "workflows__search",
        "instance_groups__search"
    ],
  ```
  
  PHASE 3: keys, give by object key names for data.actions.GET
    - type is given for each key which we could use to help craft the value

  PHASE 4: after key postfix operators can be

**TODO: will need to figure out which ones we support**

  - exact: Exact match (default lookup if not specified).
  - iexact: Case-insensitive version of exact.
  - contains: Field contains value.
  - icontains: Case-insensitive version of contains.
  - startswith: Field starts with value.
  - istartswith: Case-insensitive version of startswith.
  - endswith: Field ends with value.
  - iendswith: Case-insensitive version of endswith.
  - regex: Field matches the given regular expression.
  - iregex: Case-insensitive version of regex.
  - gt: Greater than comparison.
  - gte: Greater than or equal to comparison.
  - lt: Less than comparison.
  - lte: Less than or equal to comparison.
  - isnull: Check whether the given field or related object is null; expects a boolean value.
  - in: Check whether the given field's value is present in the list provided; expects a list of items.

  PHASE 5: The value.  Based on options, we can give hints or validation based on type of value (like number fields don't accept "foo" or whatever)
