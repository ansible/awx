## Introduction
Starting from Tower 3.3, OAuth2 will be used as the new means of token-based authentication. Users
will be able to manage OAuth2 tokens as well as applications, a server-side representation of API
clients used to generate tokens. With OAuth2, a user can authenticate by passing a token as part of
the HTTP authentication header. The token can be scoped to have more restrictive permissions on top of
the base RBAC permissions of the user.  Refer to [RFC 6749](https://tools.ietf.org/html/rfc6749) for
more details of OAuth2 specification.

## Basic Usage

To get started using OAuth2 tokens for accessing the browsable API using OAuth2, this document will walk through the steps of acquiring a token and using it.  

1. Make an application with `authorization_grant_type` set to 'password'. HTTP POST the following to the `/api/v2/applications/`  endpoint (supplying your own `organization-id`):
```
{
    "name": "Admin Internal Application",
    "description": "For use by secure services & clients. ",
    "client_type": "confidential",
    "redirect_uris": "",
    "authorization_grant_type": "password",
    "skip_authorization": false,
    "organization": <organization-id>
}
```
2. Make a token with a POST to the `/api/v2/tokens/` endpoint:
```
{
    "description": "My Access Token",
    "application": <application-id>,
    "scope": "write"
}
```
This will return a `<token-value>` that you can use to authenticate with for future requests (this will not be shown again)

3. Use token to access a resource.  We will use `curl` to demonstrate this:
```
curl -H "Authorization: Bearer <token-value>" -X GET https://<awx>/api/v2/users/
```
> The `-k` flag may be needed if you have not set up a CA yet and are using SSL.  

This token can be revoked by making a DELETE on the detail page for that token.  All you need is that token's id.  For example:
```
curl -ku <user>:<password> -X DELETE https://<awx>/api/v2/tokens/<pk>/
```

Similarly, using a token:
```
curl -H "Authorization: Bearer <token-value>" -X DELETE https://<awx>/api/v2/tokens/<pk>/ -k
```


## More Information

#### Managing OAuth2 Applications and Tokens

Applications and tokens can be managed as a top-level resource at `/api/v2/applications` and
`/api/v2/tokens`. These resources can also be accessed respective to the user at
`/api/v2/users/N/<resource>`.  Applications can be created by making a POST to either `api/v2/applications`
or `/api/v2/users/N/applications`.  

Each OAuth2 application represents a specific API client on the server side. For an API client to use the API via an application token,
it must first have an application and issue an access token.  

Individual applications will be accessible via their primary keys:
`/api/v2/applications/<pk>/`. Here is a typical application:
```
{
    "id": 1,
    "type": "o_auth2_application",
    "url": "/api/v2/applications/1/",
    "related": {
        "user": "/api/v2/users/1/",
        "tokens": "/api/v2/applications/1/tokens/",
        "activity_stream": "/api/v2/applications/1/activity_stream/"
    },
    "summary_fields": {
        "user": {
            "id": 1,
            "username": "root",
            "first_name": "",
            "last_name": ""
        },
        "tokens": {
            "count": 1,
            "results": [
                {
                    "scope": "read",
                    "token": "*************",
                    "id": 2
                }
            ]
        }
    },
    "created": "2018-02-20T23:06:43.215315Z",
    "modified": "2018-02-20T23:06:43.215375Z",
    "name": "Default application for root",
    "user": 1,
    "client_id": "BIyE720WAjr14nNxGXrBbsRsG0FkjgeL8cxNmIWP",
    "client_secret": "OdO6TMNAYxUVv4HLitLOnRdAvtClEV8l99zlb8EJEZjlzVNaVVlWiKXicznLDeANwu5qRgeQRvD3AnuisQGCPXXRCx79W1ARQ5cSmc9mrU1JbqW7nX3IZYhLIFgsDH8u",
    "client_type": "confidential",
    "redirect_uris": "",
    "authorization_grant_type": "password",
    "skip_authorization": false
},
```
In the above example, `user` is the primary key of the user associated to this application and `name` is
 a human-readable identifier for the application. The other fields, like `client_id` and
`redirect_uris`, are mainly used for OAuth2 authorization, which will be covered later in the 'Using
OAuth2 Token System' section.

Fields `client_id` and `client_secret` are immutable identifiers of applications, and will be
generated during creation; Fields `user` and `authorization_grant_type`, on the other hand, are
*immutable on update*, meaning they are required fields on creation, but will become read-only after
that.

**On RBAC side:**
- System admins will be able to see and manipulate all applications in the system;
- Organization admins will be able to see and manipulate all applications belonging to Organization
  members;
- Other normal users will only be able to see, update and delete their own applications, but
  cannot create any new applications.

Tokens, on the other hand, are resources used to actually authenticate incoming requests and mask the
permissions of the underlying user. Tokens can be created by POSTing to `/api/v2/tokens/`
endpoint by providing `application` and `scope` fields to point to related application and specify
token scope; or POSTing to `/api/v2/applications/<pk>/tokens/` by providing only `scope`, while
the parent application will be automatically linked.

Individual tokens will be accessible via their primary keys at
`/api/v2/tokens/<pk>/`. Here is a typical token:
```
{
    "id": 4,
    "type": "o_auth2_access_token",
    "url": "/api/v2/tokens/4/",
    "related": {
        "user": "/api/v2/users/1/",
        "application": "/api/v2/applications/1/",
        "activity_stream": "/api/v2/tokens/4/activity_stream/"
    },
    "summary_fields": {
        "application": {
            "id": 1,
            "name": "Default application for root",
            "client_id": "mcU5J5uGQcEQMgAZyr5JUnM3BqBJpgbgL9fLOVch"
        },
        "user": {
            "id": 1,
            "username": "root",
            "first_name": "",
            "last_name": ""
        }
    },
    "created": "2018-02-23T14:39:32.618932Z",
    "modified": "2018-02-23T14:39:32.643626Z",
    "description": "App Token Test",
    "user": 1,
    "token": "*************",
    "refresh_token": "*************",
    "application": 1,
    "expires": "2018-02-24T00:39:32.618279Z",
    "scope": "read"
},
```
For an OAuth2 token, the only fully mutable fields are `scope` and `description`. The `application`
field is *immutable on update*, and all other fields are totally immutable, and will be auto-populated
during creation.
* `user` - this field corresponds to the user the token is created for
* `expires` will be generated according to Tower configuration setting `OAUTH2_PROVIDER`
* `token` and `refresh_token` will be auto-generated to be non-clashing random strings.  

Both application tokens and personal access tokens will be shown at the `/api/v2/tokens/`
endpoint.  Personal access tokens can be identified by the `application` field being `null`.  

**On RBAC side:**
- A user will be able to create a token if they are able to see the related application;
- The System Administrator is able to see and manipulate every token in the system;
- Organization admins will be able to see and manipulate all tokens belonging to Organization
  members;
  System Auditors can see all tokens and applications
- Other normal users will only be able to see and manipulate their own tokens.
> Note: Users can only see the token or refresh-token _value_ at the time of creation ONLY.  

#### Using OAuth2 Token System for Personal Access Tokens (PAT)
The most common usage of OAuth2 is authenticating users. The `token` field of a token is used
as part of the HTTP authentication header, in the format `Authorization: Bearer <token field value>`.  This _Bearer_
token can be obtained by doing a curl to the `/api/o/token/` endpoint. For example:  
```
curl -ku <user>:<password> -H "Content-Type: application/json" -X POST \
-d '{"description":"Tower CLI", "application":null, "scope":"write"}' \
https://<awx>/api/v2/users/1/personal_tokens/ | python -m json.tool
```
Here is an example of using that PAT to access an API endpoint using `curl`:
```
curl -H "Authorization: Bearer kqHqxfpHGRRBXLNCOXxT5Zt3tpJogn" http://<awx>/api/v2/credentials/
```

According to OAuth2 specification, users should be able to acquire, revoke and refresh an access
token. In AWX the equivalent, and easiest, way of doing that is creating a token, deleting
a token, and deleting a token quickly followed by creating a new one.

The specification also provides standard ways of doing this. RFC 6749 elaborates
on those topics, but in summary, an OAuth2 token is officially acquired via authorization using
authorization information provided by applications (special application fields mentioned above).
There are dedicated endpoints for authorization and acquiring tokens. The `token` endpoint
is also responsible for token refresh, and token revoke can be done by the dedicated token revoke endpoint.

In AWX, our OAuth2 system is built on top of
[Django Oauth Toolkit](https://django-oauth-toolkit.readthedocs.io/en/latest/), which provides full
support on standard authorization, token revoke and refresh. AWX implements them and puts related
endpoints under `/api/o/` endpoint. Detailed examples on the most typical usage of those endpoints
are available as description text of `/api/o/`. See below for information on Application Access Token usage.  
> Note: The `/api/o/` endpoints can only be used for application tokens, and are not valid for personal access tokens.  


#### Token Scope Mask Over RBAC System

The scope of an OAuth2 token is a space-separated string composed of keywords like 'read' and 'write'.
These keywords are configurable and used to specify permission level of the authenticated API client.
For the initial OAuth2 implementation, we use the most simple scope configuration, where the only
valid scope keywords are 'read' and 'write'.

Read and write scopes provide a mask layer over the RBAC permission system of AWX. In specific, a
'write' scope gives the authenticated user the full permissions the RBAC system provides, while 'read'
scope gives the authenticated user only read permissions the RBAC system provides.

For example, if a user has admin permission to a job template, he/she can both see and modify, launch
and delete the job template if authenticated via session or basic auth. On the other hand, if the user
is authenticated using OAuth2 token, and the related token scope is 'read', the user can only see but
not manipulate or launch the job template, despite being an admin. If the token scope is
'write' or 'read write', she can take full advantage of the job template as its admin.  Note that 'write'
implies 'read' as well.  


## Application Functions

This page lists OAuth2 utility endpoints used for authorization, token refresh and revoke.
Note endpoints other than `/api/o/authorize/` are not meant to be used in browsers and do not
support HTTP GET. The endpoints here strictly follow
[RFC specs for OAuth2](https://tools.ietf.org/html/rfc6749), so please use that for detailed
reference. Below are some examples to demonstrate the typical usage of these endpoints in
AWX context (note that the AWX net location defaults to `http://localhost:8013` in these examples).


#### Application Using `authorization code` Grant Type

This application grant type is intended to be used when the application is executing on the server.  To create
an application named `AuthCodeApp` with the `authorization-code` grant type,
make a POST to the `/api/v2/applications/` endpoint:
```text
{
    "name": "AuthCodeApp",
    "user": 1,
    "client_type": "confidential",
    "redirect_uris": "http://<awx>/api/v2",
    "authorization_grant_type": "authorization-code",
    "skip_authorization": false
}
```
You can test the authorization flow out with this new application by copying the `client_id` and URI link into the
homepage [here](http://django-oauth-toolkit.herokuapp.com/consumer/) and click submit. This is just a simple test
application `Django-oauth-toolkit` provides.

From the client app, the user makes a GET to the Authorize endpoint with the `response_type`,
`client_id`, `redirect_uris`, and `scope`.  AWX will respond with the authorization `code` and `state`
to the `redirect_uri` specified in the application. The client application will then make a POST to the
`api/o/token/` endpoint on AWX with the `code`, `client_id`, `client_secret`, `grant_type`, and `redirect_uri`.
AWX will respond with the `access_token`, `token_type`, `refresh_token`, and `expires_in`. For more
information on testing this flow, refer to [django-oauth-toolkit](http://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_01.html#test-your-authorization-server).


#### Application Using `password` Grant Type

This is also called the `resource owner credentials grant`. This is for use by users who have
native access to the web app. This should be used when the client is the Resource owner.  Suppose
we have an application `Default Application` with grant type `password`:
```text
{
    "id": 6,
    "type": "application",
    ...
    "name": "Default Application",
    "user": 1,
    "client_id": "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l",
    "client_secret": "fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569eIaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo",
    "client_type": "confidential",
    "redirect_uris": "",
    "authorization_grant_type": "password",
    "skip_authorization": false
}
```

Login is not required for `password` grant type, so we can simply use `curl` to acquire a personal access token
via `/api/o/token/`:
```bash
curl -X POST \
  -d "grant_type=password&username=<username>&password=<password>&scope=read" \
  -u "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l:fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569e
IaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo" \
  http://<awx>/api/o/token/ -i
```
In the above POST request, parameters `username` and `password` are the username and password of the related
AWX user of the underlying application, and the authentication information is of format
`<client_id>:<client_secret>`, where `client_id` and `client_secret` are the corresponding fields of
underlying application.

Upon success, the access token, refresh token and other information are given in the response body in JSON
format:
```text
HTTP/1.1 200 OK
Server: nginx/1.12.2
Date: Tue, 05 Dec 2017 16:48:09 GMT
Content-Type: application/json
Content-Length: 163
Connection: keep-alive
Content-Language: en
Vary: Accept-Language, Cookie
Pragma: no-cache
Cache-Control: no-store
Strict-Transport-Security: max-age=15768000

{"access_token": "9epHOqHhnXUcgYK8QanOmUQPSgX92g", "token_type": "Bearer", "expires_in": 315360000000, "refresh_token": "jMRX6QvzOTf046KHee3TU5mT3nyXsz", "scope": "read"}
```


## Token Functions

#### Refresh an Existing Access Token

Suppose we have an existing access token with refresh token provided:
```text
{
    "id": 35,
    "type": "access_token",
    ...
    "user": 1,
    "token": "omMFLk7UKpB36WN2Qma9H3gbwEBSOc",
    "refresh_token": "AL0NK9TTpv0qp54dGbC4VUZtsZ9r8z",
    "application": 6,
    "expires": "2017-12-06T03:46:17.087022Z",
    "scope": "read write"
}
```
The `/api/o/token/` endpoint is used for refreshing the access token:
```bash
curl -X POST \
  -d "grant_type=refresh_token&refresh_token=AL0NK9TTpv0qp54dGbC4VUZtsZ9r8z" \
  -u "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l:fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569eIaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo" \
  http://<awx>/api/o/token/ -i
```
In the above POST request, `refresh_token` is provided by `refresh_token` field of the access token
above. The authentication information is of format `<client_id>:<client_secret>`, where `client_id`
and `client_secret` are the corresponding fields of underlying related application of the access token.

Upon success, the new (refreshed) access token with the same scope information as the previous one is
given in the response body in JSON format:
```text
HTTP/1.1 200 OK
Server: nginx/1.12.2
Date: Tue, 05 Dec 2017 17:54:06 GMT
Content-Type: application/json
Content-Length: 169
Connection: keep-alive
Content-Language: en
Vary: Accept-Language, Cookie
Pragma: no-cache
Cache-Control: no-store
Strict-Transport-Security: max-age=15768000

{"access_token": "NDInWxGJI4iZgqpsreujjbvzCfJqgR", "token_type": "Bearer", "expires_in": 315360000000, "refresh_token": "DqOrmz8bx3srlHkZNKmDpqA86bnQkT", "scope": "read write"}
```
Internally, the refresh operation deletes the existing token and a new token is created immediately
after, with information like scope and related application identical to the original one. We can
verify by checking the new token is present and the old token is deleted at the `/api/v2/tokens/` endpoint.


#### Revoke an Access Token

##### Alternatively Revoke Using the /api/o/revoke-token/ Endpoint

Revoking an access token by this method is the same as deleting the token resource object, but it allows you to delete a token by providing its token value, and the associated `client_id` (and `client_secret` if the application is `confidential`).  For example:
```bash
curl -X POST -d "token=rQONsve372fQwuc2pn76k3IHDCYpi7" \
  -u "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l:fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569eIaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo" \
  http://<awx>/api/o/revoke_token/ -i
```
`200 OK` means a successful delete.

We can verify the effect by checking if the token is no longer present
at `/api/v2/tokens/`.


## Acceptance Criteria

* All CRUD operations for OAuth2 applications and tokens should function as described.
* RBAC rules applied to OAuth2 applications and tokens should behave as described.
* A default application should be auto-created for each new user.
* Incoming requests using unexpired OAuth2 token correctly in authentication header should be able
  to successfully authenticate themselves.
* Token scope mask over RBAC should work as described.
* Tower configuration setting `OAUTH2_PROVIDER` should be configurable and function as described.
* `/api/o/` endpoint should work as expected. In specific, all examples given in the description
  help text should be working (a user following the steps should get expected result).
