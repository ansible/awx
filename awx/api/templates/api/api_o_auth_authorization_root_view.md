# Token Handling using OAuth2

This page lists OAuth 2 utility endpoints used for authorization, token refresh and revoke.
Note endpoints other than `/api/o/authorize/` are not meant to be used in browsers and do not
support HTTP GET. The endpoints here strictly follow
[RFC specs for OAuth2](https://tools.ietf.org/html/rfc6749), so please use that for detailed
reference. Note AWX net location default to `http://localhost:8013` in examples:


## Create Token for an Application using Authorization code grant type
Given an application "AuthCodeApp" of grant type `authorization-code`, 
from the client app, the user makes a GET to the Authorize endpoint with 

* `response_type`
* `client_id`
* `redirect_uris`
* `scope`  

AWX will respond with the authorization `code` and `state`
to the redirect_uri specified in the application. The client application will then make a POST to the
`api/o/token/` endpoint on AWX with

* `code`
* `client_id`
* `client_secret`
* `grant_type`
* `redirect_uri`

AWX will respond with the `access_token`, `token_type`, `refresh_token`, and `expires_in`. For more
information on testing this flow, refer to [django-oauth-toolkit](http://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_01.html#test-your-authorization-server).


## Create Token for an Application using Password grant type

Log in is not required for `password` grant type, so a simple `curl` can be used to acquire a personal access token
via `/api/o/token/` with 

* `grant_type`: Required to be "password"
* `username`
* `password`
* `client_id`: Associated application must have grant_type "password"
* `client_secret`

For example:

```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=<username>&password=<password>&scope=read" \
  -u "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l:fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569e
IaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo" \
  http://localhost:8013/api/o/token/ -i
```
In the above post request, parameters `username` and `password` are username and password of the related
AWX user of the underlying application, and the authentication information is of format
`<client_id>:<client_secret>`, where `client_id` and `client_secret` are the corresponding fields of
underlying application.

Upon success, access token, refresh token and other information are given in the response body in JSON
format:

```text
{
"access_token": "9epHOqHhnXUcgYK8QanOmUQPSgX92g", 
"token_type": "Bearer", 
"expires_in": 31536000000, 
"refresh_token": "jMRX6QvzOTf046KHee3TU5mT3nyXsz", 
"scope": "read"
}
```


## Refresh an existing access token

The `/api/o/token/` endpoint is used for refreshing access token:
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&refresh_token=AL0NK9TTpv0qp54dGbC4VUZtsZ9r8z" \
  -u "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l:fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569eIaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo" \
  http://localhost:8013/api/o/token/ -i
```
In the above post request, `refresh_token` is provided by `refresh_token` field of the access token
above. The authentication information is of format `<client_id>:<client_secret>`, where `client_id`
and `client_secret` are the corresponding fields of underlying related application of the access token.

Upon success, the new (refreshed) access token with the same scope information as the previous one is
given in the response body in JSON format:
```text
{
"access_token": "NDInWxGJI4iZgqpsreujjbvzCfJqgR", 
"token_type": "Bearer", 
"expires_in": 31536000000, 
"refresh_token": "DqOrmz8bx3srlHkZNKmDpqA86bnQkT", 
"scope": "read write"
}
```
Internally, the refresh operation deletes the existing token and a new token is created immediately
after, with information like scope and related application identical to the original one. We can
verify by checking the new token is present at the `api/v2/tokens` endpoint.  

## Revoke an access token
Revoking an access token is the same as deleting the token resource object. 
Revoking is done by POSTing to `/api/o/revoke_token/` with the token to revoke as parameter:

```bash
curl -X POST -d "token=rQONsve372fQwuc2pn76k3IHDCYpi7" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l:fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569eIaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo" \
  http://localhost:8013/api/o/revoke_token/ -i
```
`200 OK` means a successful delete.


