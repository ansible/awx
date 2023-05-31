# Bulk Host Create

This endpoint allows the client to create multiple hosts and associate them with an inventory. They may do this by providing the inventory ID and a list of json that would normally be provided to create hosts.

Example:

    {
        "inventory": 1,
        "hosts": [
            {"name": "example1.com", "variables": "ansible_connection: local"},
            {"name": "example2.com"}
        ]
    }

Return data:

    {
        "url": "/api/v2/inventories/3/hosts/",
        "hosts": [
            {
                "name": "example1.com",
                "enabled": true,
                "instance_id": "",
                "description": "",
                "variables": "ansible_connection: local",
                "id": 1255,
                "url": "/api/v2/hosts/1255/",
                "inventory": "/api/v2/inventories/3/"
            },
            {
                "name": "example2.com",
                "enabled": true,
                "instance_id": "",
                "description": "",
                "variables": "",
                "id": 1256,
                "url": "/api/v2/hosts/1256/",
                "inventory": "/api/v2/inventories/3/"
            }
        ]
    }
