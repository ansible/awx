export default
    function InventoryUpdate(PromptForPasswords, LaunchJob, Rest, ProcessErrors, Alert, Wait) {
        return function (params) {

            var scope = params.scope,
            url = params.url,
            inventory_source;

            if (scope.removeUpdateSubmitted) {
                scope.removeUpdateSubmitted();
            }
            scope.removeUpdateSubmitted = scope.$on('UpdateSubmitted', function () {
                Wait('stop');
                if (scope.socketStatus === 'error') {
                    Alert('Sync Started', '<div>The request to start the inventory sync process was submitted. ' +
                    'To monitor the status refresh the page by clicking the <i class="fa fa-refresh"></i> button.</div>', 'alert-info', null, null, null, null, true);
                    if (scope.refreshGroups) {
                        // inventory detail page
                        scope.refreshGroups();
                    }
                    else if (scope.refresh) {
                        scope.refresh();
                    }
                }
            });

            if (scope.removeStartTheUpdate) {
                scope.removeStartTheUpdate();
            }
            scope.removeStartTheUpdate = scope.$on('StartTheUpdate', function(e, passwords) {
                LaunchJob({ scope: scope, url: url, passwords: passwords, callback: 'UpdateSubmitted' });
            });

            // Check to see if we have permission to perform the update and if any passwords are needed
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
            .then(({data}) => {
                if(params.updateAllSources) {
                    scope.$emit('StartTheUpdate', {});
                }
                else {
                    inventory_source = data;
                    if (data.can_update) {
                        scope.$emit('StartTheUpdate', {});
                    } else {
                        Wait('stop');
                        Alert('Error Launching Sync', 'Unable to execute the inventory sync. Please contact your system administrator.',
                        'alert-danger');
                    }
                }
            })
            .catch(({data, status}) => {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to get inventory source ' + url + ' GET returned: ' + status });
                });
            };
    }

InventoryUpdate.$inject =
    [   'PromptForPasswords',
        'LaunchJob',
        'Rest',
        'ProcessErrors',
        'Alert',
        'Wait'
    ];
