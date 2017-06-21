export default
    function RelaunchInventory(Wait, Rest, InventoryUpdate, ProcessErrors, GetBasePath) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                url = GetBasePath('inventory_sources') + id + '/';
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    InventoryUpdate({
                        scope: scope,
                        url: data.related.update
                    });
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' +
                        url + ' GET returned: ' + status });
                });
        };
    }

RelaunchInventory.$inject =
    [   'Wait', 'Rest',
        'InventoryUpdate', 'ProcessErrors', 'GetBasePath'
    ];
