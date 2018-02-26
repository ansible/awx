# Handling Personal Access Tokens (PAT) using OAuth2

This page lists OAuth utility endpoints used for authorization, token refresh and revoke.
Note endpoints other than `/api/o/authorize/` are not meant to be used in browsers and do not
support HTTP GET. The endpoints here strictly follow
[RFC specs for OAuth2](https://tools.ietf.org/html/rfc6749), so please use that for detailed
reference. The `implicit` grant type can only be used to acquire a access token if the user is already logged in via session authentication, as that confirms that the user is authorized to create an access token. Here we give some examples to demonstrate the typical usage of these endpoints in
AWX context (Note AWX net location default to `http://localhost:8013` in examples):


## Authorization using application of grant type `implicit`
Suppose we have an application `admin's app` of grant type `implicit`:
```text
{
    "id": 1,
    "type": "application",
    "related": {
    ...
    "name": "admin's app",
    "user": 1,
    "client_id": "L0uQQWW8pKX51hoqIRQGsuqmIdPi2AcXZ9EJRGmj",
    "client_secret": "9Wp4dUrUsigI8J15fQYJ3jn0MJHLkAjyw7ikBsABeWTNJbZwy7eB2Xro9ykYuuygerTPQ2gIF2DCTtN3kurkt0Me3AhanEw6peRNvNLs1NNfI4f53mhX8zo5JQX0BKy5",
    "client_type": "confidential",
    "redirect_uris": "http://localhost:8013/api/",
    "authorization_grant_type": "implicit",
    "skip_authorization": false
}
```

In API browser, first make sure the user is logged in via session auth, then visit authorization
endpoint with given parameters:
```text
http://localhost:8013/api/o/authorize/?response_type=token&client_id=L0uQQWW8pKX51hoqIRQGsuqmIdPi2AcXZ9EJRGmj&scope=read
```
Here the value of `client_id` should be the same as that of `client_id` field of underlying application.
On success, an authorization page should be displayed asking the logged in user to grant/deny the access token.
Once the user clicks on 'grant', the API browser will try POSTing to the same endpoint with the same parameters in POST body, on success a 302 redirect will be returned:
```text
HTTP/1.1 302 Found
Connection:keep-alive
Content-Language:en
Content-Length:0
Content-Type:text/html; charset=utf-8
Date:Tue, 05 Dec 2017 20:36:19 GMT
Location:http://localhost:8013/api/#access_token=0lVJJkolFTwYawHyGkk7NTmSKdzBen&token_type=Bearer&state=&expires_in=36000&scope=read
Server:nginx/1.12.2
Strict-Transport-Security:max-age=15768000
Vary:Accept-Language, Cookie

```
By inspecting the fragment part of redirect URL given by `Location` header, we can get access token
(given by `access_token` key) as well as other standard fields specified in OAuth spec. Internally
an OAuth token is created under the given application. Verify by
`GET /api/v2/me/oauth/tokens/?token=0lVJJkolFTwYawHyGkk7NTmSKdzBen`
```text
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
...

{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 2,
            "type": "access_token",
            ...
            "user": 1,
            "token": "0lVJJkolFTwYawHyGkk7NTmSKdzBen",
            "refresh_token": "",
            "application": 1,
            "expires": "2017-12-06T06:36:19.743062Z",
            "scope": "read"
        }
    ]
}
```

## Authorization using application of grant type `password`
Suppose we have an application `Default Application` with grant type `password`:
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

Log in is not required for `password` grant type, so we can simply use `curl` to acquire a personal access token
via `/api/o/token/`:
```bash
curl -X POST \
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

{"access_token": "9epHOqHhnXUcgYK8QanOmUQPSgX92g", "token_type": "Bearer", "expires_in": 36000, "refresh_token": "jMRX6QvzOTf046KHee3TU5mT3nyXsz", "scope": "read"}
```


## Refresh an existing access token
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
The `/api/o/token/` endpoint is used for refreshing access token:
```bash
curl -X POST \
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

{"access_token": "NDInWxGJI4iZgqpsreujjbvzCfJqgR", "token_type": "Bearer", "expires_in": 36000, "refresh_token": "DqOrmz8bx3srlHkZNKmDpqA86bnQkT", "scope": "read write"}
```
Internally, the refresh operation deletes the existing token and a new token is created immediately
after, with information like scope and related application identical to the original one. We can
verify by checking the new token is present
```text
GET /api/v2/me/oauth/tokens/?token=NDInWxGJI4iZgqpsreujjbvzCfJqgR

HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept
X-API-Node: awx
X-API-Query-Count: 4
X-API-Query-Time: 0.004s
X-API-Time: 0.021s

{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 36,
            "type": "access_token",
            ...
            "user": 1,
            "token": "NDInWxGJI4iZgqpsreujjbvzCfJqgR",
            "refresh_token": "DqOrmz8bx3srlHkZNKmDpqA86bnQkT",
            "application": 6,
            "expires": "2017-12-06T03:54:06.181917Z",
            "scope": "read write"
        }
    ]
}
```
and the old token is deleted.
```text
GET /api/v2/me/oauth/tokens/?token=omMFLk7UKpB36WN2Qma9H3gbwEBSOc

HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept
X-API-Node: awx
X-API-Query-Count: 2
X-API-Query-Time: 0.003s
X-API-Time: 0.018s

{
    "count": 0,
    "next": null,
    "previous": null,
    "results": []
}
```

## Revoke an access token
Revoking an access token is the same as deleting the token resource object. Suppose we have
an existing token to revoke:
```text
{
    "id": 30,
    "type": "access_token",
    "url": "/api/v2/me/oauth/tokens/30/",
    ...
    "user": null,
    "token": "rQONsve372fQwuc2pn76k3IHDCYpi7",
    "refresh_token": "",
    "application": 6,
    "expires": "2017-12-06T03:24:25.614523Z",
    "scope": "read"
}
```
Revoking is conducted by POSTing to `/api/o/revoke_token/` with the token to revoke as parameter:
```bash
curl -X POST -d "token=rQONsve372fQwuc2pn76k3IHDCYpi7" \
  -u "gwSPoasWSdNkMDtBN3Hu2WYQpPWCO9SwUEsKK22l:fI6ZpfocHYBGfm1tP92r0yIgCyfRdDQt0Tos9L8a4fNsJjQQMwp9569eIaUBsaVDgt2eiwOGe0bg5m5vCSstClZmtdy359RVx2rQK5YlIWyPlrolpt2LEpVeKXWaiybo" \
  http://localhost:8013/api/o/revoke_token/ -i
```
`200 OK` means a successful delete.
```text
HTTP/1.1 200 OK
Server: nginx/1.12.2
Date: Tue, 05 Dec 2017 18:05:18 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 0
Connection: keep-alive
Vary: Accept-Language, Cookie
Content-Language: en
Strict-Transport-Security: max-age=15768000

```
We can verify the effect by checking if the token is no longer present.
```text
GET /api/v2/me/oauth/tokens/?token=rQONsve372fQwuc2pn76k3IHDCYpi7

HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept
X-API-Node: awx
X-API-Query-Count: 3
X-API-Query-Time: 0.003s
X-API-Time: 0.098s



{
    "count": 0,
    "next": null,
    "previous": null,
    "results": []
}
```
