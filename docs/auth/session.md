## Introduction
Before Tower 3.3, auth token is used as the main authentication method. Starting from Tower 3.3 and
API v2, session-based authentication will take the place as the main authentication, while auth token
will be replaced by OAuth tokens also introduced in 3.3.

Session authentication is a safer way of utilizing HTTP(S) cookies:

Theoretically, user can provide authentication information, like username and password, as part of the
`Cookie` header, but this method is vulnerable to cookie hijacks, where crackers can see and steal user
information from cookie payload.

Session authentication, on the other hand, sets a single `sessionid` cookie, called 'session'. Session
is *a random string which will be mapped to user authentication informations by server*. Crackers who
hijacks cookie will only get session itself, which does not imply any critical user info, valid only for
a limited time, and can be revoked at any time.

## Usage

Before a user can ever use sessions for authentication, a session has to be acquired. Sessions
in AWX are acquired/revoked via POST/DELETE to `/api/<version>/user_session/` endpoint.

In order to acquire a session, user should post to `/user_session/` with JSON body of the format:
```
{
  "username": "<user's username>",
  "password": "<user's password>"
}
```
If any input field is missing, or the username/password provided is invalid, a 400 will return with
fail reason specified; If authentication is successful, 201 will return with session information.
Session is provided as a return `Set-Cookie` header. Here is a typical one:
```
Set-Cookie: sessionid=lwan8l5ynhrqvps280rg5upp7n3yp6ds; expires=Tue, 21-Nov-2017 16:33:13 GMT; httponly; Max-Age=1209600; Path=/
```
Any client should follow the standard rules of [cookie protocol](https://tools.ietf.org/html/rfc6265) to
parse that header to obtain information about the session, such as session cookie name (`sessionid`),
session cookie value, expiration date, duration, etc.

After a valid session is acquired, a client should provide session as a cookie for subsequent requests
in order to be authenticated. like
```
Cookie: sessionid=lwan8l5ynhrqvps280rg5upp7n3yp6ds; ...
```

A session will be invalid after certain amount of time. Also a logged-in user can log out by revoking
the valid session in use. In specific, issue a DELETE request to `/user_session/`. Make sure the session
is included in cookie, otherwise this will be a no-op. When success, 204 is returned, with `Set-Cookie`
header used to expire the session cookie. User should no longer try using an invalid/revoked session.

The duration of a session is constant. However, user can extend the expiration date of a valid session
by performing session acquire with the session provided.

A Tower configuration setting, `AUTH_TOKEN_PER_USER`, is used to set the maximum number of valid sessions
a user can have aw the same time. For example, if `AUTH_TOKEN_PER_USER` is set to 3, while the same user
is logged in via 5 different places, and thus have 5 valid sessions available at the same time, the
earliest 2 (5 - 3) sessions created will be invalidated. Tower will try broadcasting, via websocket, to
all available clients. The websocket message body will contain a list of invalidated sessions. If a
client finds its session in that list, it should try logging out.

Authenticating a websocket connect using session in Tower is identical to that of normal HTTP(S) requests,
which is described earlier.

## Acceptance Criteria
* `/user_session/` endpoint should work as expected.
* `AUTH_TOKEN_PER_USER`, as well as related session over-limit control, should work as expected.
* User should be able to authenticate both HTTPS(S) request and websocket connect using valid sessions.
* User should not be able to authenticate either HTTPS(S) request or websocket connect using invalid
  sessions.
* No other existing behavior, like job run, inventory update or callback receiver, should be any
  different from current ones.
