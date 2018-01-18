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

Note a default new application will be created for each new user. So each new user is supposed to see
at least one application available to them.

Tokens, on the other hand, are resources used to actually authenticate incoming requests and mask the
permissions of underlying user. Tokens can be created by POSTing to `/api/v2/tokens/`
endpoint by providing `application` and `scope` fields to point to related application and specify
token scope; or POSTing to `/api/applications/<pk>/tokens/` by providing only `scope`, while
the parent application will be automatically linked.

# More Docs Coming Soon
