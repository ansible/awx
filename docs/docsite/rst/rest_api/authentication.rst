******************************************
Authentication Methods Using the API
******************************************

.. index::
   pair: session; authentication
   pair: basic; authentication

This chapter describes basic and session authentication methods, the best use case for each, and examples:

.. contents::
    :local:

AWX is designed for organizations to centralize and control their automation with a visual dashboard for out-of-the box control while providing a REST API to integrate with your other tooling on a deeper level. AWX supports a number of authentication methods to make it easy to embed AWX into existing tools and processes to help ensure the right people can access AWX resources.

.. _api_session_auth:

Session Authentication
======================

Session authentication is used when logging in directly to AWX’s API or UI to manually create resources (inventory, project, job template) and launch jobs in the browser. With this method, you can remain logged in for a prolonged period of time, not just for that HTTP request, but for instance, when browsing the UI or API in a browser like Chrome or Firefox. When a user logs in, a session cookie is created, which enables the user to remain logged in when navigating to different pages within AWX. Below represents the communication that occurs between the client and server in a session.

.. image:: ../common/images/session-auth-architecture.png

Using the curl tool, you can see the activity that occurs when you log into AWX.

1. GET to the ``/api/login/`` endpoint to grab the ``csrftoken`` cookie.

.. code-block:: text

	curl -k -c - https://<awx-host>/api/login/

	localhost	FALSE	/	FALSE	0   csrftoken
	AswSFn5p1qQvaX4KoRZN6A5yer0Pq0VG2cXMTzZnzuhaY0L4tiidYqwf5PXZckuj

2. POST to the ``/api/login/`` endpoint with username, password, and X-CSRFToken=<token-value>.

.. code-block:: text

	curl -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  	--referer https://<awx-host>/api/login/ \
  	-H 'X-CSRFToken: K580zVVm0rWX8pmNylz5ygTPamgUJxifrdJY0UDtMMoOis5Q1UOxRmV9918BUBIN' \
  	--data 'username=root&password=reverse' \
  	--cookie 'csrftoken=K580zVVm0rWX8pmNylz5ygTPamgUJxifrdJY0UDtMMoOis5Q1UOxRmV9918BUBIN' \
  	https://<awx-host>/api/login/ -k -D - -o /dev/null

All of this is done by the AWX when you log in to the UI or API in the browser, and should only be used when authenticating in the browser.

A typical response might look like:

.. code-block:: text

	Server: nginx
	Date: <current date>
	Content-Type: text/html; charset=utf-8
	Content-Length: 0
	Connection: keep-alive
	Location: /accounts/profile/
	X-API-Session-Cookie-Name: awx_sessionid
	Expires: <date>
	Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private
	Vary: Cookie, Accept-Language, Origin
	Session-Timeout: 1800
	Content-Language: en
	X-API-Total-Time: 0.377s
	X-API-Request-Id: 700826696425433fb0c8807cd40c00a0
	Access-Control-Expose-Headers: X-API-Request-Id
	Set-Cookie: userLoggedIn=true; Path=/
	Set-Cookie: current_user=<user cookie data>; Path=/
	Set-Cookie: csrftoken=<csrftoken>; Path=/; SameSite=Lax
	Set-Cookie: awx_sessionid=<your session id>; expires=<date>; HttpOnly; Max-Age=1800; Path=/; SameSite=Lax
	Strict-Transport-Security: max-age=15768000


When a user is successfully authenticated with this method, the server will respond with a header called ``X-API-Session-Cookie-Name``, indicating the configured name of the session cookie. The default value is ``awx_session_id`` which you can see later in the ``Set-Cookie`` headers.

.. note::

	The session expiration time can be changed by specifying it in the ``SESSION_COOKIE_AGE`` parameter. Refer to the next section, :ref:`api_session_limits` for further detail.

.. _api_session_limits:

Working with Session Limits
----------------------------
.. index::
  single: session limits
  single: session.py
  pair: SESSIONS_PER_USER; session limits
  pair: AUTH_BASIC_ENABLED; session limits

Setting a session limit allows administrators to limit the number of simultaneous sessions per user or per IP address.

A session is created for each browser that a user uses to log in, which forces the user to log out any extra sessions after they exceed the administrator-defined maximum.

Session limits may be important, depending on your particular setup. For example, perhaps you only want a single user on your system with a single login per device (where the user could log in on his work laptop, phone, or home computer). In such a case, you would want to create a session limit equal to 1 (one). If the user logs in on his laptop, for example, then logs in using his phone, his laptop session expires (times out) and only the login on the phone persists. Proactive session limits will kick the user out when the session is idle. The default value is **-1**, which disables the maximum sessions allowed altogether, meaning you can have as many sessions without an imposed limit.

While session counts can be very limited, they can also be expanded to cover as many session logins as are needed by your organization.

When a user logs in and their login results in other users being logged out, the session limit has been reached and those users who are logged out are notified as to why the logout occurred.

.. note::
  To make the best use of session limits, disable ``AUTH_BASIC_ENABLED`` by changing the value to ``False``, as it falls outside of the scope of session limit enforcement.


Basic Authentication
====================

Basic Authentication (Basic Auth) is stateless, thus the base64-encoded ``username`` and ``password`` must be sent along with each request via the Authorization header. This can be used for API calls from curl requests, python scripts, or individual requests to the API.
Example with curl:

.. code-block:: text

   # the --user flag adds this Authorization header for us
   curl -X GET --user 'user:password' https://<awx-host>/api/v2/credentials -k -L

For more information about the Basic HTTP Authentication scheme, see `RFC 7617 <https://datatracker.ietf.org/doc/html/rfc7617>`_.

