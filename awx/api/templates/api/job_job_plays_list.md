Make a GET request to retrieve the list of aggregated play data associated with a job

## Filtering

This endpoints supports a limited filtering subset:

    ?id__in=1,2,3

Will show only the given ids.

    ?id__gt=1

Will show ids greater than the given one.

    ?id__lt=3

Will show ids less than the given one.

    ?failed=true

Will show only failed plays.  Alternatively `false` may be used.

    ?play_icontains=test

Will filter plays matching the substring `test`
