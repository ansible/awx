export default
    function CancelSourceUpdate(Empty, Rest, ProcessErrors, Alert, Wait, Find) {
        return function(params) {
            var scope = params.scope,
            id = params.id,
            inventory_source = params.inventory_source;

            // Cancel the update process
            if (Empty(inventory_source)) {
                inventory_source = Find({ list: scope.inventory_sources, key: 'id', val: id });
                scope.selected_inventory_source_id = inventory_source.id;
            }

            if (inventory_source && (inventory_source.status === 'running' || inventory_source.status === 'pending')) {
                // We found the inventory_source, and there is a running update
                Wait('start');
                Rest.setUrl(inventory_source.url);
                Rest.get()
                .then(({data}) => {
                    // Check that we have access to cancelling an update
                    var url = (data.related.current_update) ? data.related.current_update : data.related.last_update;
                    url += 'cancel/';
                    Rest.setUrl(url);
                    Rest.get()
                    .then(({data}) => {
                        if (data.can_cancel) {
                            // Cancel the update process
                            Rest.setUrl(url);
                            Rest.post()
                            .then(() => {
                                Wait('stop');
                                //Alert('Inventory Sync Canceled', 'Request to cancel the sync process was submitted to the task manger. ' +
                                //    'Click the <i class="fa fa-refresh fa-lg"></i> button to monitor the status.', 'alert-info');
                            })
                            .catch(({data, status}) => {
                                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                              msg: 'Call to ' + url + ' failed. POST status: ' + status
                                });
                            });
                        }
                        else {
                            Wait('stop');
                        }
                    })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                      msg: 'Call to ' + url + ' failed. GET status: ' + status
                        });
                    });
                })
                .catch(({data, status}) => {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                  msg: 'Call to ' + inventory_source.url + ' failed. GET status: ' + status
                    });
                });
            }
        };
    }

CancelSourceUpdate.$inject =
    [   'Empty', 'Rest', 'ProcessErrors',
        'Alert', 'Wait', 'Find'
    ];
