# Search Iteration 1 Requirements:

## DONE

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

## TODO later on in 3.6: stuff to be finished for search iteration 1 (I'll card up an issue to tackle this. I plan on doing this after I finished the awx project branch work)

- currently handleSearch in Search.jsx always appends the `__icontains` post-fix to make the filtering ux expected work right. Once we start adding number-based params we will won't to change this behavior.
- utilize new defaultSearchKey prop instead of relying on sort key
- make access have username as the default key?
- make default params only accept page, page_size and order_by
- support custom order_by being typed in the url bar
- fix up which keys are displayed in the various lists (note this will also require non-string widgetry to the right of the search key dropdown, for integers, dates, etc.)
- fix any spacing issues like collision with action buttons and overall width of the search bar

## Lists affected in 3.6 timeframe

We should update all places to use consistent handleSearch/handleSort with paginated data list pattern.  This shouldn't be too difficult to get hooked up, as the lists all inherit from PaginatedDataList, where search is hooked up.  We will need to make sure the queryset config for each list includes the searchable boolean on keys that will need to be searched for.

orgs stuff
  - org list
  - org add/edit instance groups lookup list
  - org access list
    - org user/teams list in wizard
  - org teams list
  - org notifications list
jt stuff
  - jt list
  - jt add/edit inventory, project, credentials, instance groups lookups lists
  - jt access list
    - jt user/teams list in wizard
  - jt notifications list
  - jt schedules list
  - jt completed jobs list
jobs stuff
  - jobs list

# Search code details

## Search component

Search is configured using the qsConfig in a similar way to sort. Columns are passed as an array, as defined in the screen where the list is located. You pass a bool isSearchable (an analog to isSortable) to mark that a certain key should show up in the left-hand dropdown of the search bar.

If you don't pass any columns, a default of isSearchable true will be added to a name column, which is nearly universally shared throughout the models of awx.

The component looks like this:

```
<Search
  qsConfig={qsConfig} // used to get namespace (when tags are modified 
                      // they append namespace to query params)
                      // also used to get "type" of fields (i.e. interger
                      // fields should get number picker instead of text box)
/>
```

## ListHeader component

DataListToolbar, EmptyListControls, and FilterTags components were created/moved to a new sub-component of PaginatedDataList, ListHeader. This allowed us to consolidate the logic between both lists with data (which need to show search, sort, any search tags currently active, and actions) as well as empty lists (which need to show search tags currently active so they can be removed, potentially getting you back to a "list-has-data" state, as well as a subset of options still valid (such as "add").

search and sort are passed callbacks from functions defined in ListHeader. These will be the following.

```
handleSort (sortedColumnKey, sortOrder) {
  this.pushHistoryState({
    order_by: sortOrder === 'ascending' ? sortedColumnKey : `-${sortedColumnKey}`,
    page: null,
  });
}

handleSearch (key, value, remove) {
  this.pushHistoryState({
    // ... use key and value to push a new value to the param
    // if remove false you add a new tag w key value if remove true, 
    // you are removing one
  });
}
```

Similarly, there are handleRemove and handleRemoveAll functions. All of these functions act on the react-router history using the pushHistoryState function. This causes the query params in the url to update, which in turn triggers change handlers that will re-fetch data.

## FilterTags component

Similar to the way the list grabs data based on changes to the react-router params, the FilterTags component updates when new params are added. This component is a fairly straight-forward map (only slightly complex, because it needed to do a nested map over any values with duplicate keys that were represented by an inner-array).

Currently the filter tags do not display the key, though that data is available and they could very easily do so.

## QS Updates (and supporting duplicate keys)

The logic that was updated to handle search tags can be found in the qs.js util file.

From a UX perspective, we wanted to be able to support searching on the same key multiple times (i.e. searching for things like ?foo=bar&foo=baz). We do this by creating an array of all values. i.e.:

```
{
  foo: ['bar', 'baz']
}
```

Changes to encodeQueryString and parseQueryString were made to convert between a single value string representation and multiple value array representations. Test cases were also added to qs.test.js.

In addition, we needed to make sure any changes to the params that are not handled by search (page, page_size, and order_by) were updated by replacing the single value, rather than adding multiple values with the array representation. This additional piece of the specification was made in the newly created addParams and removeParams qs functions and a few test-cases were written to verify this.

The api is coupled with the qs util through the paramsSerializer, due to the fact we need axios to support the array for duplicate key values object representation of the params to pass to the get request.  This is done where axios is configured in the Base.js file, so all requests and request types should support our array syntax for duplicate keys.

# UX considerations

**UX should be more tags always equates to more filtering.  (so "and" logic not "or")**

Also, for simple search results should be returned that partially match value (i.e. use icontains prefix)

**ALL query params namespaced and in url bar**

 - this includes lists that aren't necessarily hyperlinked, like lookup lists.
 - the reason behind this is so we can treat the url bar as the source of truth for queries always
 - currently /#/organizations/add?lookup.name=bar -> will eventually be something like /#/organizations/add?ig_lookup.name=bar
 - any params that have both a key AND value that is in the defaultParams section of the qs config should be stripped out of the search string

**django fuzzy search (?search=) is not accessible outside of "advanced search"**

  - How "search" query param works
    - in current smart search typing a term with no key utilizes search= i.e. for "foo" tag, ?search=foo is given
    - search= looks on a static list of field name "guesses" (such as name, description, etc.), as well as specific fields as defined for each endpoint (for example, the events endpoint looks for a "stdout" field as well)
    - note that search= tags are OR'd together
    - search=foo&name=bar returns items that have a name field of bar (not case insensitive) AND some text field with foo on it
    - search=foo&search=bar&name=baz returns (foo in name OR foo in description OR ...) AND (bar in name OR bar in description OR ...) AND (baz in name)
  - similarly ?related__search= looks on the static list of "guesses" for models related to the endpoint
    - the specific fields are not "searched" for related__search
    - related__search not currently used in awx ui

**a note on typing in a smart search query**

In order to not support a special "language" or "syntax" for crafting the query like we have now (and is the cause of a large amount of bugs), we will not support the old way of typing in a filter like in the current implementation of search.

Since all search bars are represented in the url, for users who want to input a string to filter results in a single step, typing directly in the url to achieve the filter is acceptable.

**a note on clicking a tag to putting it back into the search bar**

This was brought up as a nice to have when we were discussing features.  There isn't a way we would be able to know if the user created the tag from the smart search or simple search interface?  that info is not traceable using the query params as the exclusive source of truth

We have decided to not try to tackle this up front with our advanced search implementation, and may go back to this based on user feedback at a later time.

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
