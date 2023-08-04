
*********
Sorting
*********

.. index::
   pair: sorting; ordering

To provide examples that are easy to follow, the following URL is used throughout this guide:

::

    http://<server name>/api/v2/groups/


To specify that {{ model_verbose_name_plural }} are returned in a particular order, use the ``order_by`` query string parameter on the **GET** request.

::

    http://<server name>/api/v2/model_verbose_name_plural?order_by={{ order_field }}

Prefix the field name with a dash (``-``) to sort in reverse:

::

    http://<server name>/api/v2/model_verbose_name_plural?order_by=-{{ order_field }}

Multiple sorting fields may be specified by separating the field names with a comma (``,``):

::

    http://<server name>/api/v2/model_verbose_name_plural?order_by={{ order_field }},some_other_field




