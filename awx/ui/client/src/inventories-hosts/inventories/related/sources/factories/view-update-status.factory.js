export default
    function ViewUpdateStatus($state, Rest, ProcessErrors, Alert, Wait, Empty, Find) {
        return function(params) {
            var scope = params.scope,
            inventory_source_id = params.inventory_source_id,
            inventory_source = Find({ list: scope.inventory_sources, key: 'id', val: inventory_source_id });

            if (inventory_source) {
                if (Empty(inventory_source.status) || inventory_source.status === "never updated") {
                    Alert('No Status Available', '<div>An inventory sync has not been performed for the selected group. Start the process by ' +
                          'clicking the <i class="fa fa-refresh"></i> button.</div>', 'alert-info', null, null, null, null, true);
                } else {
                    Wait('start');
                    Rest.setUrl(inventory_source.url);
                    Rest.get()
                    .then(({data}) => {
                        // Get the ID from the correct summary field
                        var update_id = (data.summary_fields.current_update) ? data.summary_fields.current_update.id : data.summary_fields.last_update.id;

                        $state.go('output', { id: update_id, type: 'inventory' });
                    })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                      msg: 'Failed to retrieve inventory source: ' + inventory_source.url +
                                          ' GET returned status: ' + status });
                    });
                }
            }
        };
    }

ViewUpdateStatus.$inject =
    [   '$state', 'Rest', 'ProcessErrors',
        'Alert', 'Wait', 'Empty', 'Find'
    ];
