# Bulk Host Delete

This endpoint allows the client to delete multiple hosts from inventories.
They may do this by providing a list of hosts ID's to be deleted.

Example:

    {
        "hosts": [1, 2, 3, 4, 5]
    }

Return data:

    {
        "hosts": {
            "1": "The host a1 was deleted",
            "2": "The host a2 was deleted",
            "3": "The host a3 was deleted",
            "4": "The host a4 was deleted",
            "5": "The host a5 was deleted",
        }
    }