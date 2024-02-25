******************
Pagination
******************

.. index::
   single: pagination
   single: serializer


Responses for collections in the API are paginated. This means that while a collection may contain tens or hundreds of thousands of objects, in each web request, only a limited number of results are returned for API performance reasons.

When you get back the result for a collection you will see something similar to the following:

::

    {'count': 25, 'next': 'http://testserver/api/v2/some_resource?page=2', 'previous': None, 'results': [ ... ] }

To get the next page, simply request the page given by the 'next' sequential URL.


Use the ``page_size=XX`` query string parameter to change the number of results returned for each request. 

The ``page_size`` has a default maximum limit configured to 200, which is enforced when a user tries a value beyond it, for example, ``?page_size=1000``. However, you can change this limit by setting the value in ``/etc/awx/conf.d/<some file>.py`` to something higher, e.g. ``MAX_PAGE_SIZE=1000``.

Use the ``page`` query string parameter to retrieve a particular page of results.

::

    http://<server name>/api/v2/model_verbose_name?page_size=100&page=2


The previous and next links returned with the results will set these query string parameters automatically.

The serializer is quite efficient, but you should probably not request page sizes beyond a couple of hundred.

The user interface uses smaller values to avoid the user having to do a lot of scrolling.