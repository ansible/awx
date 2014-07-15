Make a GET request to this resource to retrieve aggregate statistics about inventory suitable for graphing.

Including fetching the number of total hosts tracked by Tower over an amount of time and the current success or
failed status of hosts which have run jobs within an Inventory.

## Parmeters and Filtering

The `period` of the data can be adjusted with:

    ?period=month

Where `month` can be replaced with `week`, or `day`.  `month` is the default.

## Results

Data about the number of hosts will be returned in the following format:

    "hosts": [
        [
            1402808400.0, 
            86743
        ], ...]

Each element contains an epoch timestamp represented in seconds and a numerical value indicating
the number of hosts that exist at a given moment

Data about failed and successfull hosts by inventory will be given as:

    {
            "sources": [
                {
                    "successful": 21, 
                    "source": "ec2", 
                    "name": "aws (Test Inventory)", 
                    "failed": 0
                }
            ], 
            "id": 2, 
            "name": "Test Inventory"
     },
