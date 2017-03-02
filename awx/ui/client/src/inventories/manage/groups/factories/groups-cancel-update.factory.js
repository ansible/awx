export default
    function GroupsCancelUpdate(Empty, Rest, ProcessErrors, Alert, Wait, Find) {
        return function(params) {
            var scope = params.scope,
            id = params.id,
            group = params.group;

            if (scope.removeCancelUpdate) {
                scope.removeCancelUpdate();
            }
            scope.removeCancelUpdate = scope.$on('CancelUpdate', function (e, url) {
                // Cancel the update process
                Rest.setUrl(url);
                Rest.post()
                .success(function () {
                    Wait('stop');
                    //Alert('Inventory Sync Cancelled', 'Request to cancel the sync process was submitted to the task manger. ' +
                    //    'Click the <i class="fa fa-refresh fa-lg"></i> button to monitor the status.', 'alert-info');
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                  msg: 'Call to ' + url + ' failed. POST status: ' + status
                    });
                });
            });

            if (scope.removeCheckCancel) {
                scope.removeCheckCancel();
            }
            scope.removeCheckCancel = scope.$on('CheckCancel', function (e, last_update, current_update) {
                // Check that we have access to cancelling an update
                var url = (current_update) ? current_update : last_update;
                url += 'cancel/';
                Rest.setUrl(url);
                Rest.get()
                .success(function (data) {
                    if (data.can_cancel) {
                        scope.$emit('CancelUpdate', url);
                        //} else {
                        //    Wait('stop');
                        //    Alert('Cancel Inventory Sync', 'The sync process completed. Click the <i class="fa fa-refresh fa-lg"></i> button to view ' +
                        //        'the latest status.', 'alert-info');
                    }
                    else {
                        Wait('stop');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                  msg: 'Call to ' + url + ' failed. GET status: ' + status
                    });
                });
            });

            // Cancel the update process
            if (Empty(group)) {
                group = Find({ list: scope.groups, key: 'id', val: id });
                scope.selected_group_id = group.id;
            }

            if (group && (group.status === 'running' || group.status === 'pending')) {
                // We found the group, and there is a running update
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                .success(function (data) {
                    scope.$emit('CheckCancel', data.related.last_update, data.related.current_update);
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                  msg: 'Call to ' + group.related.inventory_source + ' failed. GET status: ' + status
                    });
                });
            }
        };
    }

GroupsCancelUpdate.$inject =
    [   'Empty', 'Rest', 'ProcessErrors',
        'Alert', 'Wait', 'Find'
    ];
