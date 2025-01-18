### Collection that demos event_query

This can act as source code for a collection that uses the event_query thing.

It has a `meta/event_query.yml` file, which may provide you an example of how
to implement this in your own collection.

Even better, this is used to test the feature in the AWX "live" tests.

To do this, the "event_query" project references this (host_query) project
in its `collections/requirements.yml` file.
The test logic makes a copy of this folder as a git repo, so that
the file location can be used as a git source.
