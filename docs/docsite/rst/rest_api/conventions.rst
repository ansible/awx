******************
Conventions
******************

.. index::
   single: conventions
   pair: API; root directory
   pair: content type; JSON


AWX uses a standard REST API, rooted at ``/api/`` on the server. The API is versioned for compatibility reasons, and currently ``api/v2/`` is the latest available version. You can see information about what API versions are available by querying ``/api/``.

You may have to specify the content/type on **POST** or **PUT** requests accordingly.

- **PUT**: Update a specific resource (by an identifier) or a collection of resources. PUT can also be used to create a specific resource if the resource identifier is known before-hand.
- **POST**: Create a new resource. Also acts as a catch-all verb for operations that do not fit into the other categories.

All URIs  not ending with ``"/"`` receive a 301 redirect.

.. note::

    Formatting of ``extra_vars`` attached to Job Template records is preserved. YAML is returned as YAML with formatting and comments preserved, and JSON is returned as JSON.