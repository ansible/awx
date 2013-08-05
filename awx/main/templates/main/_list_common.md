The resulting data structure contains:

    {
        "count": 99, 
        "next": null, 
        "previous": null, 
        "results": [
            ...
        ]
    }

The `count` field indicates the total number of {{ model_verbose_name_plural }}
found for the given query.  The `next` and `previous` fields provides links to
additional results if there are more than will fit on a single page.  The
`results` list contains zero or more {{ model_verbose_name }} records.  

## Results

Each {{ model_verbose_name }} data structure includes the following fields:

{% include "main/_result_fields_common.md" %}

## Sorting

To specify that {{ model_verbose_name_plural }} are returned in a particular
order, use the `order_by` query string parameter on the GET request.

    ?order_by={{ order_field }}

Prefix the field name with a dash `-` to sort in reverse:

    ?order_by=-{{ order_field }}

## Pagination

Use the `page_size` query string parameter to change the number of results
returned for each request.  Use the `page` query string parameter to retrieve
a particular page of results.

    ?page_size=100&page=2

The `previous` and `next` links returned with the results will set these query
string parameters automatically.

## Filtering

Any additional query string parameters may be used to filter the list of
results returned to those matching a given value.  Only fields that exist in
the database can be used for filtering.

    ?{{ order_field }}=value

Field lookups may also be used for slightly more advanced queries, for example:

    ?{{ order_field }}__startswith=A
    ?{{ order_field }}__endsswith=C
    ?{{ order_field }}__contains=ABC
