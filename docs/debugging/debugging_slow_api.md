# Slow API Endpoint

The time it takes from the start of an HTTP request until the time the last byte arrives at the client is the full request response. If you eliminate the client entirely it is the time after the client sends the HTTP request (ending in `\n\n`) until the time the server responds with the first byte of the response.

In practice, rarely is the network bandwidth or the client bandwidth the problem. The performance culprit usually involves the word "database". i.e. under-provisioned database hardware, low database IOPS (HD vs SSD vs NVME), a poor performing query, or many fast queries that add up to be slow. Rarely is it an inefficient python algorithm. Sometimes it is row-level database lock contention.

## Is it db related?
Every API response contains the headers `X-API-Time` and `X-API-Total-Time` where `X-API-Time` <= `X-API-Total-Time`. `X-API-Time` is set by the middleware function `TimingMiddleware.process_response()`. As of writing this `TimingMiddleware` appears very close to the top of the `MIDDLEWARE` settings list. Middleware `process_response` are processed in the reverse order, thus, `TimingMiddleware.process_response()` runs very close to the end of the middleware stack and therefore should result in `X-API-Time` =~ `X-API-Total-Time`. If `X-API-Total-Time - X-API-Time` is large then their is a performance problem in a small slice of code in between the middleware response processing and the DRF response processing. If `X-API-Total-Time` and  `X-API-Time` are larger, then there is likely a performance problem and you need to enable `SQL_DEBUG` to determine if it is database related.

When `SQL_DEBUG = True` the headers `X-API-Query-Time` and `X-API-Query-Count` will be included in the response. A high `X-API-Query-Time` and `X-API-Query-Count` indicates there are many small queries that add up. A high `X-API-Query-Time` and low `X-API-Query-Count` indicates there are 1 or more expensive queries. A low `X-API-Query-Time` indicates you should look elsewhere (i.e. python algorithm or slow network).

**TL;DR** Look at headers `X-API-Time` and `X-API-Total-Time`. If large then enable `SQL_DEBUG = True` and look at `X-API-Query-Time` and `X-API-Query-Count`. If `X-API-Query-Time` or `X-API-Query-Count` are large then it is likely a database issue.

## Django Debug Toolbar (DDT)
This is a useful tool for examining per-api endpoint SQL queries, performance, headers, requests, signals, cache, logging, and more.  

To enable DDT, you need to set your `INTERNAL_IPS` to the IP address of your load balancer.  This can be overridden by creating a new settings file beginning with `local_` in `awx/settings/` (e.g. `local_overrides.py`).
This IP address can be found by making a GET to any page on the browsable API and looking for information like this in the standard output:
```
awx_1        | 14:42:08 uwsgi.1     | 172.18.0.1 GET /api/v2/tokens/ - HTTP/1.1 200
```

Allow this IP address by adding it to the `INTERNAL_IPS` variable in your new override local settings file, then navigate to the API and you should see DDT on the
right side.  If you don't see it, make sure to set `DEBUG=True`.  
> Note that enabling DDT is detrimental to the performance of AWX and adds overhead to every API request.  It is
recommended to keep this turned off when you are not using it.  

