There is a new way of exposing metrics. Instead of using redis and websockets to deliver metrics to all nodes, each node runs a metrics http server. Use this new way and remove the old redis way.
