
******************
Searching 
******************

.. index::
   single: searching

Use the search query string parameter to perform a non-case-sensitive search within all designated text fields of a model:

::

    http://<server name>/api/v2/model_verbose_name?search=findme



Search across related fields:

::

    http://<server name>/api/v2/model_verbose_name?related__search=findme

