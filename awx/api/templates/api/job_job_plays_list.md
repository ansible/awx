Make a GET request to retrieve the list of aggregated play data associated with a job

## Filtering

This endpoints supports a limited filtering subset:

    ?event_id__in=1,2,3

Will show only the given ids.

    ?event_id__gt=1

Will show ids greater than the given one.

    ?event_id__lt=3

Will show ids less than the given one.

    ?failed=true

Will show only failed plays.  Alternatively `false` may be used.

    ?play__icontains=test

Will filter plays matching the substring `test`

{% include "api/_new_in_awx.md" %}
