******************************************
Authentication Methods Using the API
******************************************

.. index::
   pair: session; authentication
   pair: basic; authentication
   pair: OAuth 2 Token; authentication
   pair: SSO; authentication

This chapter describes the numerous enterprise authentication methods, the best use case for each, and examples:

.. contents::
    :local:

AWX is designed for organizations to centralize and control their automation with a visual dashboard for out-of-the box control while providing a REST API to integrate with your other tooling on a deeper level. AWX supports a number of authentication methods to make it easy to embed AWX into existing tools and processes to help ensure the right people can access AWX resources. 

.. _api_session_auth:

Session Authentication
-----------------------

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

All of this is done by the AWX when you log in to the UI or API in the browser, and should only be used when authenticating in the browser. For programmatic integration with AWX, see :ref:`api_oauth2_auth`.

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

	The session expiration time can be changed by specifying it in the ``SESSION_COOKIE_AGE`` parameter. Refer to :ref:`ag_session_limits` for further detail.

Basic Authentication
---------------------

Basic Authentication (Basic Auth) is stateless, thus the base64-encoded ``username`` and ``password`` must be sent along with each request via the Authorization header. This can be used for API calls from curl requests, python scripts, or individual requests to the API. :ref:`api_oauth2_auth` is recommended for accessing the API when at all possible.  

Example with curl:

.. code-block:: text

   curl -X GET -H 'Authorization: Basic dXNlcjpwYXNzd29yZA==’ https://<awx-host>/api/v2/credentials -k -L

   # the --user flag adds this Authorization header for us
   curl -X GET --user 'user:password' https://<awx-host>/api/v2/credentials -k -L

For more information about the Basic HTTP Authentication scheme, see `RFC 7617 <https://datatracker.ietf.org/doc/html/rfc7617>`_.

.. note::

	You can disable the Basic Auth for security purposes from the Miscellaneous Authentication settings of the AWX UI Settings menu:

	.. image:: ../common/images/configure-awx-auth-basic-off.png

.. _api_oauth2_auth:

OAuth 2 Token Authentication
-----------------------------

OAuth (Open Authorization) is an open standard for token-based authentication and authorization. OAuth 2 authentication is commonly used when interacting with the AWX API programmatically. Like Basic Auth, an OAuth 2 token is supplied with each API request via the Authorization header. Unlike Basic Auth, OAuth 2 tokens have a configurable timeout and are scopable. Tokens have a configurable expiration time and can be easily revoked for one user or for the entire AWX system by an admin if needed. This can be done with the :ref:`ag_manage_utility_revoke_tokens` management command, which is covered in more detail in |ata| or by using the API as explained in :ref:`ag_oauth2_token_revoke`.

.. note::

	By default, external users such as those created by SSO are not allowed to generate OAuth tokens for security purposes. This can be changed from the Miscellaneous Authentication settings of the AWX UI Settings menu:

	.. image:: ../common/images/configure-awx-external-tokens-off.png 

The different methods for obtaining OAuth 2 Access Tokens in AWX are:

- Personal access tokens (PAT)
- Application Token: Password grant type
- Application Token: Implicit grant type
- Application Token: Authorization Code grant type

For more information on the above methods, see :ref:`ag_oauth2_token_auth` in the |ata|.


First, a user needs to create an OAuth 2 Access Token in the API or in their User’s **Tokens** tab in the UI. For further detail on creating them through the UI, see :ref:`ug_users_tokens`. For the purposes of this example, use the PAT method for creating a token in the API. Upon token creation, the user can set the scope. 

.. note::

	The expiration time of the token can be configured system-wide. See :ref:`ag_use_oauth_pat` for more detail.

Token authentication is best used for any programmatic use of the AWX API, such as Python scripts or tools like curl, as in the example for creating a PAT (without an associated application) below.

**Curl Example**

.. code-block:: text

   curl -u user:password -k -X POST https://<awx-host>/api/v2/tokens/


This call will return JSON data like:

.. image:: ../common/images/api_oauth2_json_returned_token_value.png

The value of the ``token`` property is what you can now use to perform a GET request for an AWX resource, e.g., Hosts.

.. code-block:: text

	curl -k -X POST \
  	  -H “Content-Type: application/json”
  	  -H “Authorization: Bearer <oauth2-token-value>” \
  	  https://<awx-host>/api/v2/hosts/ 

Similarly, you can launch a job by making a POST to the job template that you want to launch.

.. code-block:: text

	curl -k -X POST \
  	  -H "Authorization: Bearer <oauth2-token-value>" \
  	  -H "Content-Type: application/json" \
  	  --data '{"limit" : "ansible"}' \
  	  https://<awx-host>/api/v2/job_templates/14/launch/ 


**Python Example**

`awxkit <https://pypi.org/project/awxkit/>`_ is an open source tool that makes it easy to use HTTP requests to access the AWX API. 
You can have awxkit acquire a PAT on your behalf by using the ``awxkit login`` command. Refer to the :ref:`api_start` for more detail.

For more information on how to use OAuth 2 in AWX in the context of integrating external applications, see :ref:`ag_oauth2_token_auth` in the |ata|. 

If you need to write custom requests, you can write a Python script using `Python library requests <https://pypi.org/project/requests/>`_, like in this example:

.. code-block:: text

	import requests
	oauth2_token_value = 'y1Q8ye4hPvT61aQq63Da6N1C25jiA'   # your token value from AWX
	url = 'https://<awx-host>/api/v2/users/'
	payload = {}
	headers = {'Authorization': 'Bearer ' + oauth2_token_value,}

	# makes request to awx user endpoint
	response = requests.request('GET', url, headers=headers, data=payload,
	allow_redirects=False, verify=False)

	# prints json returned from awx with formatting
	print(json.dumps(response.json(), indent=4, sort_keys=True))


.. _api_sso_auth:

SSO Authentication
-------------------

Single sign-on (SSO) authentication methods are fundamentally different from other methods because the authentication of the user happens external to AWX, like Google SSO, Azure SSO, SAML, or GitHub. For example, with GitHub SSO, GitHub is the single source of truth, which verifies your identity based on the username and password you gave AWX.

You can configure SSO authentication using AWX inside a large organization with a central Identity Provider. Once you have configured an SSO method in AWX, a button for that SSO will be present on the login screen. If you click that button, it will redirect you to the Identity Provider, in this case GitHub, where you will present your credentials. If the Identity Provider verifies you successfully, then AWX will make a user linked to your GitHub user (if this is your first time logging in via this SSO method), and log you in.

For the various types of supported SSO authentication methods, see :ref:`ag_social_auth` and :ref:`ag_ent_auth` in the |ata|.

