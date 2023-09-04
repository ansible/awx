******************
Read-only Fields
******************

.. index::
   single: read-only fields


Certain fields in the REST API are marked read-only. These usually
include the URL of a resource, the ID, and occasionally some internal
fields. For instance, the ``'created\_by'`` attribute of each object
indicates which user created the resource, and cannot be edited.

If you post some values and notice that they are not changing, these fields may be read-only.
