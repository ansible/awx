export default
    function RelaunchInventory(Find, Wait, Rest, InventoryUpdate, ProcessErrors, GetBasePath) {
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
                        url: data.related.update,
                        group_name: data.summary_fields.group.name,
                        group_source: data.source,
                        tree_id: null,
                        group_id: data.group
                    });
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' +
                        url + ' GET returned: ' + status });
                });
        };
    }

RelaunchInventory.$inject =
    [   'Find', 'Wait', 'Rest',
        'InventoryUpdate', 'ProcessErrors', 'GetBasePath'
    ];
