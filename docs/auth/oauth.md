## Introduction
Starting from Tower 3.3, OAuth 2 will be used as the new means of token-based authentication. Users
will be able to manage OAuth 2 tokens as well as applications, a server-side representation of API
clients used to generate tokens. With OAuth 2, a user can authenticate by passing a token as part of 
the HTTP authentication header. The token can be scoped to have more restrictive permissions on top of
the base RBAC permissions of the user.  Refer to [RFC 6749](https://tools.ietf.org/html/rfc6749) for 
more details of OAuth 2 specification.

## Usage

#### Managing OAuth 2 applications and tokens
Applications and tokens can be managed as a top-level resource at `/api/<version>/applications` and 
`/api/<version>/tokens`. These resources can also be accessed respective to the user at 
`/api/<version>/users/N/<resource>`.  Applications can be created by making a POST to either `api/<version>/applications`
or `/api/<version>/users/N/applications`.  

Each OAuth 2 application represents a specific API client on the server side. For an API client to use the API, 
it must first have an application, and issue an access token.  

Individual applications will be accessible via their primary keys:
`/api/<version>/applications/<primary key of an application>/`. Here is a typical application:
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
                    "token": "**************",
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
In the above example, `user` is the primary key of the user this application associates to and `name` is
 a human-readable identifier for the application. The other fields, like `client_id` and
`redirect_uris`, are mainly used for OAuth 2 authorization, which will be covered later in the 'Using
OAuth token system' section.

Fields `client_id` and `client_secret` are immutable identifiers of applications, and will be
generated during creation; Fields `user` and `authorization_grant_type`, on the other hand, are
*immutable on update*, meaning they are required fields on creation, but will become read-only after
that.

On RBAC side:
- system admins will be able to see and manipulate all applications in the system;
- Organization admins will be able to see and manipulate all applications belonging to Organization
  members;
- Other normal users will only be able to see, update and delete their own applications, but
  cannot create any new applications.



Tokens, on the other hand, are resources used to actually authenticate incoming requests and mask the
permissions of the underlying user. Tokens can be created by POSTing to `/api/v2/tokens/`
endpoint by providing `application` and `scope` fields to point to related application and specify
token scope; or POSTing to `/api/applications/<pk>/tokens/` by providing only `scope`, while
the parent application will be automatically linked.

Individual tokens will be accessible via their primary keys:
`/api/<version>/me/oauth/tokens/<primary key of a token>/`. Here is a typical token:
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
    "refresh_token": "**************",
    "application": 1,
    "expires": "2018-02-24T00:39:32.618279Z",
    "scope": "read"
},
```
For an OAuth 2 token, the only fully mutable field is `scope`. The `application` field is *immutable
on update*, and all other fields are totally immutable, and will be auto-populated during creation:
`user` field will be the `user` field of related application; `expires` will be generated according
to Tower configuration setting `OAUTH2_PROVIDER`; `token` and `refresh_token` will be auto-generated 
to be non-crashing random strings.  Both application tokens and personal access tokens will be shown
at the `/api/v2/tokens/` endpoint.  Personal access tokens can be identified by the applications field 
being `null`.  

On RBAC side:
- A user will be able to create a token if they are able to see the related application;
- System admin is able to see and manipulate every token in the system; 
- Organization admins will be able to see and manipulate all tokens belonging to Organization
  members;
- Other normal users will only be able to see and manipulate their own tokens.
> Note: Users can only see the token or refresh-token _value_ at the time of creation ONLY.  

#### Using OAuth 2 token system as a Personal Access Token (PAT)
The most common usage of OAuth 2 is authenticating users. The `token` field of a token is used
as part of the HTTP authentication header, in the format `Authorization: Bearer <token field value>`.  This _Bearer_
token can be obtained by doing a curl to the `/api/o/token/` endpoint as shown in `api_o_auth_authorization_root_view.md`.  

Here is an example of using that PAT to access an API endpoint using `curl`:
```
curl -H "Authorization: Bearer kqHqxfpHGRRBXLNCOXxT5Zt3tpJogn" http://localhost:8013/api/v2/credentials/
```

According to OAuth 2 specification, users should be able to acquire, revoke and refresh an access
token. In AWX the equivalent, and the easiest, way of doing that is creating a token, deleting
a token, and deleting a token quickly followed by creating a new one.

The specification also provides standard ways of doing this though. RFC 6749 elaborates
on those topics, but in summary, an OAuth 2 token is officially acquired via authorization using
authorization information provided by applications (special application fields mentioned above).
There are dedicated endpoints for authorization and acquiring tokens. The `token` endpoint
is also responsible for token refresh, and token revoke can be done by the dedicated token revoke endpoint.

In AWX, our OAuth 2 system is built on top of
[Django Oauth Toolkit](https://django-oauth-toolkit.readthedocs.io/en/latest/), which provides full
support on standard authorization, token revoke and refresh. AWX implements them and puts related
endpoints under `/api/o/` endpoint. Detailed examples on the most typical usage of those endpoints
are available as description text of `/api/o/`.

#### Token scope mask over RBAC system
The scope of an OAuth 2 token is a space-separated string composed of keywords like 'read' and 'write'.
These keywords are configurable and used to specify permission level of the authenticated API client.
For the initial OAuth 2 implementation, we use the most simple scope configuration, where the only
valid scope keywords are 'read' and 'write'.

Read and write scopes provide a mask layer over the RBAC permission system of AWX. In specific, a
'write' scope gives the authenticated user the full permissions the RBAC system provides, while 'read'
scope gives the authenticated user only read permissions the RBAC system provides.

For example, if a user has admin permission to a job template, he/she can both see and modify, launch
and delete the job template if authenticated via session or basic auth. On the other hand, if the user
is authenticated using OAuth 2 token, and the related token scope is 'read', the user can only see but
not manipulate or launch the job template, despite being an admin. If the token scope is
'write' or 'read write', she can take full advantage of the job template as its admin.  Note, that 'write'
implies 'read' as well.  

## Acceptance Criteria
* All CRUD operations for OAuth 2 applications and tokens should function as described.
* RBAC rules applied to OAuth applications and tokens should behave as described.
* A default application should be auto-created for each new user.
* Incoming requests using unexpired OAuth 2 token correctly in authentication header should be able
  to successfully authenticate themselves.
* Token scope mask over RBAC should work as described.
* Tower configuration setting `OAUTH2_PROVIDER` should be configurable and function as described.
* `/api/o/` endpoint should work as expected. In specific, all examples given in the description
  help text should be working (user following the steps should get expected result).
