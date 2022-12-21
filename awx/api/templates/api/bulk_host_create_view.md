# Bulk Host Create

This endpoint allows the client to create multiple hosts and associate them with an inventory. They may do this by providing the inventory ID and a list of json that would normally be provided to create hosts.

Example:

```
{
"inventory": 1,
"hosts": [
    {"name": "example1.com"},
    {"name": "example2.com"}
]

}
```
