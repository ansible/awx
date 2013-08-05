Make a POST request to this resource with `username` and `password` fields to
obtain an authentication token to use for subsequent requests.

Example JSON to POST (content type is `application/json`):

    {"username": "user", "password": "my pass"}

Example form data to post (content type is `application/x-www-form-urlencoded`):

    username=user&password=my%20pass

If the username and password provided are valid, the response will contain a
`token` field with the authentication token to use:

    {"token": "8f17825cf08a7efea124f2638f3896f6637f8745"}

Otherwise, the response will indicate the error that occurred and return a 4xx
status code.

For subsequent requests, pass the token via the HTTP `Authenticate` request
header:

    Authenticate: Token 8f17825cf08a7efea124f2638f3896f6637f8745
