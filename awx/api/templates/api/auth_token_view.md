Make a POST request to this resource with `username` and `password` fields to
obtain an authentication token to use for subsequent requests.

Example JSON to POST (content type is `application/json`):

    {"username": "user", "password": "my pass"}

Example form data to post (content type is `application/x-www-form-urlencoded`):

    username=user&password=my%20pass

If the username and password provided are valid, the response will contain a
`token` field with the authentication token to use and an `expires` field with
the timestamp when the token will expire:

    {
        "token": "8f17825cf08a7efea124f2638f3896f6637f8745",
        "expires": "2013-09-05T21:46:35.729Z"
    }

Otherwise, the response will indicate the error that occurred and return a 4xx
status code.

For subsequent requests, pass the token via the HTTP `Authorization` request
header:

    Authorization: Token 8f17825cf08a7efea124f2638f3896f6637f8745

The auth token is only valid when used from the same remote address and user
agent that originally obtained it.

Each request that uses the token for authentication will refresh its expiration
timestamp and keep it from expiring.  A token only expires when it is not used
for the configured timeout interval (default 1800 seconds).
