## Introduction
Starting from Tower 3.3, OAuth 2 will be used as the new means of token-based authentication. Users
will be able to manage OAuth tokens as well as applications, a server-side representation of API
clients used to generate tokens. By including an OAuth token as part of the HTTP authentication
header, a user will be able to authenticate herself and gain more restrictive permissions on top of
the base RBAC permissions of the user. The degree of restriction is controllable by the scope of an
OAuth token. Refer to [RFC 6749](https://tools.ietf.org/html/rfc6749) for more details of OAuth 2
specification.

## Usage

#### Managing OAuth applications and tokens
The root of OAuth management endpoints is `/api/<version>/me/oauth/`, which gives a list of endpoint
roots for managing individual type of OAuth resources: OAuth application under
`/api/<version>/me/oauth/applications/` and OAuth token under `/api/<version>/me/oauth/tokens/`. The
reason for OAuth management endpoints to be under `/api/<version>/me/` is because, as an authentication
approach, OAuth resources will only take effect to the underlying user.

Each OAuth application belongs to a specific user, and is used to represent a specific API client
on the server side. For example, if AWX user Alice wants to make her `curl` command to talk to
AWX, the first thing is creating a new application and probably name it `Alice' curl client`.

Individual applications will be accessible via their primary keys:
`/api/<version>/me/oauth/applications/<primary key of an application>/`. Here is a typical application:
```
{
    "id": 1,
    "type": "application",
    "url": "/api/v2/me/oauth/applications/1/",
    "related": {
        "user": "/api/v2/users/1/",
        "tokens": "/api/v2/me/oauth/applications/1/tokens/",
        "activity_stream": "/api/v2/me/oauth/applications/1/activity_stream/"
    },
    "summary_fields": {
        "user": {
            "id": 1,
            "username": "admin",
            "first_name": "",
            "last_name": ""
        },
        "tokens": {
            "count": 13,
            "results": [
                {
                    "token": "UdglJ1IkG3YrkzPWkEIwBqWP2xL8X7",
                    "id": 16
                },
                ...
            ]
        }
    },
    "created": "2017-12-07T16:08:21.341687Z",
    "modified": "2017-12-07T16:08:21.342015Z",
    "name": "admin's app",
    "user": 1,
    "client_id": "l7VbJdYxqKzoewQR7iZAYkiUI7AdqQhJuiAF4TqJ",
    "client_secret": "gsplwGti48nJhs5dJ9IMJ0BqN3LvwvFPFgbrQzhXz4bT2oOJBmoCj2egpAUF6Ivme1LFLYAeLwYkmj8AVHEkpYfYxMvK6LTNJG8nO2AIGt7l6MCgj9oD5cgwLvsfGxl2",
    "client_type": "confidential",
    "redirect_uris": "",
    "authorization_grant_type": "password",
    "skip_authorization": false
}
```
In the above example, `user` is the underlying user this application associates to; `name` can be
used as a human-readable identifier of the application. The rest fields, like `client_id` and
`redirect_uris`, are mainly used for OAuth authorization, which will be covered later in 'Using
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
  cannot create any new application.

Note a default new application will be created for each new user. So each new user is supposed to see
at least one application available to them.

Tokens, on the other hand, are resources used to actually authenticate incoming requests and mask the
permissions of underlying user. There are two ways of creating a token: POSTing to `/me/oauth/tokens/`
endpoint by providing `application` and `scope` fields to point to related application and specify
token scope; or POSTing to `/me/oauth/applications/<pk>/tokens/` by providing only `scope`, while
the parent application will be automatically linked.

Individual tokens will be accessible via their primary keys:
`/api/<version>/me/oauth/tokens/<primary key of a token>/`. Here is a typical token:
```
{
    "id": 17,
    "type": "access_token",
    "url": "/api/v2/me/oauth/tokens/17/",
    "related": {
        "user": "/api/v2/users/1/",
        "application": "/api/v2/me/oauth/applications/4/",
        "activity_stream": "/api/v2/me/oauth/tokens/17/activity_stream/"
    },
    "summary_fields": {
        "application": {
            "id": 4,
            "name": "admin's token",
            "client_id": "D6SwhKbfp2LuUjkmiUpMMYFyNqhpv5PTVci7eXTT"
        },
        "user": {
            "id": 1,
            "username": "admin",
            "first_name": "",
            "last_name": ""
        }
    },
    "created": "2017-12-12T16:48:10.489550Z",
    "modified": "2017-12-12T16:48:10.522189Z",
    "user": 1,
    "token": "kqHqxfpHGRRBXLNCOXxT5Zt3tpJogn",
    "refresh_token": "miZq3hqSugvYxhzdQYJIBDgIHxJPnT",
    "application": 4,
    "expires": "2017-12-13T02:48:10.488180Z",
    "scope": "read"
}
```
For an OAuth token, the only fully mutable field is `scope`. `application` field is *immutable
on update*, and all other fields are totally immutable, and will be auto-populated during creation:
`user` field will be the `user` field of related application; `expires` will be generated according
to Tower configuration setting `OAUTH2_PROVIDER`; `token` and `refresh_token` will be auto-
generated to be non-crashing random strings.

On RBAC side:
- A user will be able to create a token if she is able to see the related application;
- System admin is able to see and manipulate every token in the system;
- Organization admins will be able to see and manipulate all tokens belonging to Organization
  members;
- Other normal users will only be able to see and manipulate their own tokens.

#### Using OAuth token system
The most significant usage of OAuth is authenticating users. `token` field of a token is used
as part of HTTP authentication header, in the format `Authorization: Bearer <token field value>`.
Here is a `curl` command example:
```
curl -H "Authorization: Bearer kqHqxfpHGRRBXLNCOXxT5Zt3tpJogn" http://localhost:8013/api/v2/credentials/
```

According to OAuth 2 specification, users should be able to acquire, revoke and refresh an access
token. In AWX the equivalent, and the easiest, way of doing that is creating a token, deleting
a token, and deleting a token quickly followed by creating a new one.

On the other hand, the specification also provides standard ways of doing those. RFC 6749 elaborates
on those topics, but in summary, an OAuth token is officially acquired via authorization using
authorization information provided by applications (special application fields mentioned above).
There are dedicated endpoints for authorization and token acquire; The token acquire endpoint
is also responsible for token refresh; and token revoke is done by dedicated token revoke endpoint.

In AWX, our OAuth system is built on top of
[Django Oauth Toolkit](https://django-oauth-toolkit.readthedocs.io/en/latest/), which provides full
support on standard authorization, token revoke and refresh. AWX reuses them and puts related
endpoints under `/api/o/` endpoint. Detailed examples on some most typical usage of those endpoints
are available as description text of `/api/o/`.

#### Token scope mask over RBAC system
The scope of an OAuth token is a space-separated string composed of keywords like 'read' and 'write'.
These keywords are configurable and used to specify permission level of the authenticated API client.
For the initial OAuth implementation, we use the most simple scope configuration, where the only
valid scope keywords are 'read' and 'write'.

Read and write scopes provide a mask layer over the RBAC permission system of AWX. In specific, a
'write' scope gives the authenticated user full permissions the RBAC system provides, while 'read'
scope gives the authenticated user only read permissions the RBAC system provides.

For example, if a user has admin permission to a job template, she can both see and modify, launch
and delete the job template if authenticated via session or basic auth. On the other hand, if she
is authenticated using OAuth token, and the related token scope is 'read', she can only see but
not manipulate or launch the job template, despite she has admin role over it; if the token scope is
'write' or 'read write', she can take full advantage of the job template as its admin.

## Acceptance Criteria
* All CRUD operations for OAuth applications and tokens should function as described.
* RBAC rules applied to OAuth applications and tokens should behave as described.
* A default application should be auto-created for each new user.
* Incoming requests using unexpired OAuth token correctly in authentication header should be able
  to successfully authenticate themselves.
* Token scope mask over RBAC should work as described.
* Tower configuration setting `OAUTH2_PROVIDER` should be configurable and function as described.
* `/api/o/` endpoint should work as expected. In specific, all examples given in the description
  help text should be working (user following the steps should get expected result).
