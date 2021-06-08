{% include "api/sub_list_api_view.md" %}
{% ifmeth GET %}
## Special limit feature for event list views

Use the `limit` query string parameter to opt out of the pagination keys.
Doing this can improve response times for jobs that produce a large volume
of outputs.

    ?limit=25

This will set the page size to 25 and the `previous` and `next` keys will be
omitted from the response data. The data structure will look like this.

    {
        "results": [
            ...
        ]
    }


{% endifmeth %}
