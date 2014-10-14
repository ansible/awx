Make a GET request to retrieve the list of aggregated task data associated with the play given by event_id.

`event_id` is a required query parameter and must match the job event id of the parent play in order to receive the list of tasks associated with the play

## Filtering

This endpoints supports a limited filtering subset:

    ?event_id__in=1,2,3

Will show only the given task ids under the play given by `event_id`.

    ?event_id__gt=1

Will show ids greater than the given one.

    ?event_id__lt=3

Will show ids less than the given one.

    ?failed=true

Will show only failed plays.  Alternatively `false` may be used.

    ?task__icontains=test

Will filter tasks matching the substring `test`

{% include "api/_new_in_awx.md" %}
