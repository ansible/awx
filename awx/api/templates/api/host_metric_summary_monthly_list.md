# Intended Use Case

To get summaries from a certain day or earlier, you can filter this
endpoint in the following way.

    ?date__gte=2023-01-01

This will return summaries that were produced on that date or later.
These host metric monthly summaries should be automatically produced
by a background task that runs once each month.

{% include "api/list_api_view.md" %}
